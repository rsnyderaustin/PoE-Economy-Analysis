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

        self.engine = sqlalchemy.create_engine(db_url)
        self.connection = self.engine.connect()
        self.inspector = inspect(self.engine)

        self._initialized = True

    def _add_missing_columns(self, table_name: str, new_data: dict):
        table_col_names = self._fetch_column_names(table_name)
        logging.info(f"Current col names: {table_col_names}")

        new_cols = set(new_data.keys())
        missing_col_names = set(col for col in new_cols if col not in table_col_names)
        logging.info(f"Missing col names: {missing_col_names}")

        missing_col_data = {k: v for k, v in new_data.items() if k in missing_col_names}
        missing_col_dtypes = utils.determine_col_dtypes(raw_data=missing_col_data)

        logging.info("Starting loop to add missing columns")
        with self.engine.begin() as conn:
            for col, dtype in missing_col_dtypes.items():
                logging.info(f"Adding missing column {col}")

                alter_stmt = text(f'ALTER TABLE {table_name} ADD COLUMN "{col}" {dtype};')
                conn.execute(alter_stmt)

        self.inspector = inspect(self.engine)

    def _count_table_rows(self, table_name: str):
        result = self.connection.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        count = result.scalar()

        return count

    def _fetch_column_names(self, table_name: str):
        return set(col['name'] for col in self.inspector.get_columns(table_name))

    def insert_data(self, table_name: str, data: dict):

        data = {utils.format_column_name(col): val for col, val in data.items()}

        utils.validate_dict_lists(data)
        self._add_missing_columns(table_name=table_name,
                                  new_data=data)

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
