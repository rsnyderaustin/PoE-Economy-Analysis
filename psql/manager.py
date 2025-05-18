import logging

import sqlalchemy
from sqlalchemy import text, inspect

from shared import shared_utils
from shared.env_loading import EnvLoader
from . import utils


class PostgreSqlManager:
    def __new__(cls):
        if not hasattr(cls, '_instance'):
            cls._instance = super(PostgreSqlManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, '_initialized', False):
            return

        e = EnvLoader()
        user = e.get_env("PSQL_USERNAME")
        passw = e.get_env("PSQL_PASSWORD")
        host = e.get_env("PSQL_HOST")
        db_n = e.get_env("PSQL_DATABASE")
        ip = e.get_env("PSQL_IP")
        db_url = f"postgresql+psycopg2://{user}:{passw}@{ip}:{host}/{db_n}"
        print(db_url)

        """self.engine = sqlalchemy.create_engine(db_url)
        self.connection = self.engine.connect()
        self.inspector = inspect(self.engine)"""

        self._initialized = True

    def _add_columns(self, table_name: str, col_dtypes: dict):
        """

        :param table_name:
        :param col_dtypes: Keys are column names, and values are the data type
        :return:
        """
        logging.info(f"Adding columns {list(col_dtypes.keys())}")
        with self.engine.begin() as conn:
            for col, dtype in col_dtypes.items():
                # Add column as TEXT, you can customize type as needed
                alter_stmt = text(f'ALTER TABLE {table_name} ADD COLUMN "{col}" {dtype};')
                conn.execute(alter_stmt)
                print(f"Added column: {col}")

    def _count_table_rows(self, table_name: str):
        result = self.connection.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        count = result.scalar()

        return count

    def insert_data(self, table_name: str, data: dict):

        utils.validate_dict_lists(data)

        logging.info(f"Insert data length: {shared_utils.determine_dict_length(data)}")

        data = {utils.format_column_name(col): val for col, val in data.items()}
        table_col_names = set(self.inspector.get_columns(table_name))
        missing_col_names = [col for col in data.keys() if col not in table_col_names]

        if missing_col_names:
            logging.info(f"Current col names:\n{table_col_names}\nMissing col names:{missing_col_names}")
            missing_col_dtypes = utils.determine_col_dtypes(raw_data=data,
                                                            col_names=missing_col_names)
            self._add_columns(table_name=table_name,
                              col_dtypes=missing_col_dtypes)
            self.inspector = inspect(self.engine)  # Have to refresh inspector cache after changing schema

        cols = ', '.join(f'"{k}"' for k in data.keys())
        placeholders = ', '.join(f":{k}" for k in data.keys())
        insert_stmt = text(f'INSERT INTO {table_name} ({cols}) VALUES ({placeholders})')

        # When inserting into psql via SqlAlchemy, the data has to be a list of dicts
        formatted_data = utils.format_data_into_rows(data)

        logging.info(f"{table_name} rows before insertion: {self._count_table_rows(table_name)}")
        with self.engine.begin() as conn:
            conn.execute(insert_stmt, formatted_data)
        logging.info(f"{table_name} rows after insertion: {self._count_table_rows(table_name)}")

    def fetch_table_data(self, table_name: str):
        with self.engine.connect() as conn:
            # Select * from your table
            result = conn.execute(text(f'SELECT * FROM {table_name}'))

            # Get column names from result metadata
            columns = result.keys()

            # Initialize dict with empty lists
            data_dict = {col: [] for col in columns}

            # Iterate over all rows
            for row in result:
                for col in columns:
                    data_dict[col].append(row[col])

            return data_dict
