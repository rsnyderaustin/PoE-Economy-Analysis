
import logging

import sqlalchemy
from sqlalchemy import text, inspect

from shared.env_loading import EnvLoader
from shared.logging import LogsHandler, LogFile
from . import utils

psql_log = LogsHandler().fetch_log(LogFile.PSQL)


class PostgreSqlManager:
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(PostgreSqlManager, cls).__new__(cls)

        return cls._instance

    def __init__(self, skip_sql=False):
        cls = self.__class__
        if cls._initialized:
            return
        cls._initialized = True

        self.skip_sql = skip_sql

        if skip_sql:
            print("Skipping SQL initialization.")
            return

        e = EnvLoader()
        user = e.get_env("PSQL_USERNAME")
        passw = e.get_env("PSQL_PASSWORD")
        port = e.get_env("PSQL_PORT")
        db_n = e.get_env("PSQL_DATABASE")
        ip = e.get_env("PSQL_IP")
        db_url = f"postgresql+psycopg2://{user}:{passw}@{ip}:{port}/{db_n}"
        print(db_url)

        self.engine = sqlalchemy.create_engine(db_url)
        self.connection = self.engine.connect()
        self.inspector = inspect(self.engine)

    def _add_missing_columns(self, table_name: str, new_data: dict):

        table_col_names = self._fetch_column_names(table_name)

        new_cols = set(new_data.keys())
        missing_col_names = set(col for col in new_cols if col not in table_col_names)
        missing_col_data = {k: v for k, v in new_data.items() if k in missing_col_names}
        missing_col_dtypes = utils.determine_col_dtypes(raw_data=missing_col_data)

        if missing_col_names:
            with self.engine.begin() as conn:
                psql_log.info(f"Adding missing '{table_name}' col names: {missing_col_names}")
                for col, dtype in missing_col_dtypes.items():
                    alter_stmt = text(f'ALTER TABLE {table_name} ADD COLUMN "{col}" {dtype};')
                    conn.execute(alter_stmt)

            self.inspector = inspect(self.engine)

    def _count_table_rows(self, table_name: str):
        with self.connection.begin():
            result = self.connection.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            count = result.scalar()

        return count

    def _fetch_column_names(self, table_name: str):
        return set(col['name'] for col in self.inspector.get_columns(table_name))

    def insert_data(self, table_name: str, data: dict):
        if self.skip_sql:
            return

        data = {utils.format_column_name(col): val for col, val in data.items()}

        utils.validate_dict_lists(data)
        self._add_missing_columns(table_name=table_name,
                                  new_data=data)

        cols = ', '.join(f'"{k}"' for k in data.keys())
        placeholders = ', '.join(f":{k}" for k in data.keys())
        insert_stmt = text(f'INSERT INTO {table_name} ({cols}) VALUES ({placeholders})')

        # When inserting into psql via SqlAlchemy, the data has to be a list of dicts
        formatted_data = utils.format_data_into_rows(data)

        rows_before = self._count_table_rows(table_name)
        with self.engine.begin() as conn:
            conn.execute(insert_stmt, formatted_data)
        logging.info(f"{table_name} PSQL rows {rows_before} -> {self._count_table_rows(table_name)}")

    def fetch_table_data(self, table_name: str) -> dict:
        if self.skip_sql:
            return dict()
        with self.engine.connect() as conn:
            # Select * from your table
            result = list(conn.execute(text(f'SELECT * FROM {table_name}')).mappings())

            cols = list(result[0].keys())
            data_dict = {col: [] for col in cols}

            for row in result:
                for col in cols:
                    data_dict[col].append(row[col])

            return data_dict

    def fetch_columns_data(self, table_name: str, columns: list[str]) -> dict:
        if self.skip_sql:
            return dict()
        
        if not columns:
            raise ValueError("No columns specified")

        cols_dict = {col: [] for col in columns}

        table_cols = self._fetch_column_names(table_name)
        missing_cols = [col for col in columns if col not in table_cols]
        present_cols = [col for col in columns if col in table_cols]
        if missing_cols:
            if not present_cols:
                psql_log.info(f"None of {missing_cols} are in Psql table '{table_name}. Returning all empty columns.")
                return cols_dict

            psql_log.info(f"{missing_cols} missing from Psql table '{table_name}'. "
                          f"Will return empty lists for those columns specifically.")

        # Very basic sanitization: quote identifiers
        quoted_columns = ', '.join(f'"{col}"' for col in present_cols)
        quoted_table = f'"{table_name}"'

        query = text(f'SELECT {quoted_columns} FROM {quoted_table}')

        with self.engine.connect() as conn:
            result = list(conn.execute(query).mappings())

            if not result:
                return cols_dict

            for row in result:
                for col in present_cols:
                    cols_dict[col].append(row[col])

            return cols_dict
