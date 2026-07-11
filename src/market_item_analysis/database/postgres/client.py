from dataclasses import dataclass
from enum import Enum
from typing import Any

import sqlalchemy
from sqlalchemy import text, inspect
from src.market_item_analysis.program_logging import LogsHandler, LogFile

from src.market_item_analysis.core.env_loader import EnvLoader

psql_log = LogsHandler().fetch_log(LogFile.PSQL)


class ValueCondition(Enum):
    GREATER_THAN = '>'
    LESS_THAN = '<'
    EQUAL_TO = '='
    NOT_EQUAL_TO = '!='

@dataclass
class QueryFilter:
    left_value: Any
    right_value: Any
    value_condition: ValueCondition

    @property
    def sql(self) -> str:
        return f"{self.left_value} {self.value_condition} {self.right_value}"


class PostgresQuery:

    def __init__(self):
        self.conditions = []
        self.params = []

    def filter_by_age(self):


class PostgresDatabaseUrl:

    def __init__(self,
                 user: str | None = None,
                 password: str | None = None,
                 port: str | None = None,
                 database: str | None = None,
                 ip_address: str | None = None):
        e = EnvLoader()

        self.user = user or e.get_env("PSQL_USERNAME")
        self.password = password or e.get_env("PSQL_PASSWORD")
        self.port = port or e.get_env("PSQL_PORT")
        self.database = database or e.get_env("PSQL_DATABASE")
        self.ip_address = ip_address or e.get_env("PSQL_IP")

    @property
    def url(self):
        return f"postgresql+psycopg2://{self.user}:{self.password}@{self.ip_address}:{self.port}/{self.database}"

@dataclass(frozen=True)
class PostgresColumn:
    name: str
    dtype: str


class PostgresClient:
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(PostgresClient, cls).__new__(cls)

        return cls._instance

    def __init__(self, skip_sql=False):
        cls = self.__class__
        if cls._initialized:
            return
        cls._initialized = True

        self.skip_sql = skip_sql

        if skip_sql:
            psql_log.info("Skipping SQL initialization.")
            return

        psql_log.info(f"Connecting to PSQL database.")

        database_url = PostgresDatabaseUrl()
        self.engine = sqlalchemy.create_engine(database_url.url)
        self.connection = self.engine.connect()
        self.inspector = inspect(self.engine)

        psql_log.info(f"Connected to PSQL database at: {database_url.url}")

    def row_count(self, table_name: str) -> int:
        with self.connection.begin():
            result = self.connection.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            count = result.scalar()

        return count

    def column_names(self, table_name: str) -> list[str]:
        return list(col['name'] for col in self.inspector.get_columns(table_name))

    def add_columns(self, table_name: str, columns: list[PostgresColumn]):
        add_cols_expression = '\n'.join([f"ADD COLUMN \"{col.name}\" {col.dtype}" for col in columns])
        alter_statement = text(f'ALTER TABLE {table_name}\n{add_cols_expression}')

        with self.engine.begin() as conn:
            conn.execute(alter_statement)

        self.inspector = inspect(self.engine)

    def insert_data(self, table_name: str, data: list[dict]):
        if not data:
            return

        col_names = list(data[0].keys())
        comma_delimited_col_names = ', '.join(f'"{col_name}"' for col_name in col_names)
        placeholders = ', '.join(f":{col_name}" for col_name in col_names)
        insert_stmt = text(f'INSERT INTO {table_name} ({comma_delimited_col_names}) VALUES ({placeholders})')

        with self.engine.begin() as conn:
            conn.execute(insert_stmt, data)

    def table_data(self,
                   table_name: str,
                   column_names: list[str] | None = None,
                   where: list[str] | None = None) -> dict:
        columns = [col.upper() for col in column_names]

        if self.skip_sql:
            return dict()

        quoted_table = f'"{table_name}"'
        if columns:
            table_cols = self.column_names(table_name)
            missing_cols = [col for col in columns if col not in table_cols]
            if missing_cols:
                error_msg = f"Columns requested but not present in table: {missing_cols}\nColumns in table: {table_cols}"
                psql_log.error(error_msg)
                raise ValueError(error_msg)

            # Very basic sanitization: quote identifiers
            quoted_columns = ', '.join(f'"{col}"' for col in columns)

            query = text(f'SELECT {quoted_columns} FROM {quoted_table}')
        else:
            query = text(f'SELECT * FROM {quoted_table}')

        if where:
            where_sql = 'AND '.join([w for w in where])
            query += f" {where_sql}"

        with self.engine.connect() as conn:
            result = list(conn.execute(query).mappings())

            cols_dict = {col: [] for col in columns}

            if not result:
                return cols_dict

            for row in result:
                for col in columns:
                    cols_dict[col].append(row[col])

            return cols_dict

