
from typing import Iterable
import sqlalchemy
from sqlalchemy import text, inspect
from shared.env_loading import EnvLoader, EnvVariable

from . import utils


class PostgreSqlManager:
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(PostgreSqlManager, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        if getattr(self, '_initialized', False):
            return

        e = EnvLoader()
        user = e.get_env(EnvVariable.PSQL_USERNAME)
        passw = e.get_env(EnvVariable.PSQL_PASSWORD)
        host = e.get_env(EnvVariable.PSQL_HOST)
        db_n = e.get_env(EnvVariable.PSQL_DATABASE)
        db_url = f"postgresql+psycopg2://{user}:{passw}@localhost:{host}/{db_n}"

        self.engine = sqlalchemy.create_engine(db_url)
        self.connection = self.engine.connect()
        self.inspector = inspect(self.engine)

        self._initialized = True

    def _fetch_table_column_names(self, table_name: str):
        return [col['name'] for col in self.inspector.get_columns(table_name)]

    def _add_columns(self, table_name: str, col_dtypes: dict):
        """

        :param table_name:
        :param col_dtypes: Keys are column names, and values are the data type
        :return:
        """
        with self.engine.begin() as conn:
            for col, dtype in col_dtypes.items():
                # Add column as TEXT, you can customize type as needed
                alter_stmt = text(f'ALTER TABLE {table_name} ADD COLUMN "{col}" {dtype};')
                conn.execute(alter_stmt)
                print(f"Added column: {col}")

    def insert_data(self, table_name: str, data: dict):
        if not all([isinstance(data_val, Iterable) for col_name, data_val in data.items()]):
            raise TypeError(f"Insert data function currently only supports inserting iterables as values.")

        table_col_names = self._fetch_table_column_names(table_name)
        missing_col_names = [col for col in data.keys() if col not in table_col_names]
        missing_col_dtypes = utils.determine_col_dtypes(raw_data=data,
                                                        col_names=missing_col_names)
        self._add_columns(table_name=table_name,
                          col_dtypes=missing_col_dtypes)

        cols = ', '.join(f'"{k}"' for k in data.keys())
        placeholders = ', '.join(f":{k}" for k in data.keys())
        insert_stmt = text(f'INSERT INTO {table_name} ({cols}) VALUES ({placeholders})')
        with self.engine.begin() as conn:
            conn.execute(insert_stmt, **data)

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
