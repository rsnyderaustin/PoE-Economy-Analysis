from typing import Iterable

from sqlalchemy import text

from src.market_item_analysis.database.postgres import PostgresClient
from src.market_item_analysis.database.postgres.python_to_postgres_dtype import PythonToPostgresDtype

psql_log = LogsHandler().fetch_log(log_e=LogFile.PSQL)


class PostgresInsertableData:

    def __init__(self, data: dict):
        """

        :param data: Formatted as {col: [values]}
        """
        self.validate(data=data)
        self.columns = self.create_columns(data=data)
        self.data = self.format(data=data)
    
    @classmethod
    def format(cls, data: dict):
        data = {col[:55].lower(): val for col, val in data.items()}

        # When inserting into postgres via SqlAlchemy, the data has to be a list of dicts
        columns = list(data.keys())
        values = zip(*data.values())

        # Build the list of dictionaries
        formatted_data = [dict(zip(columns, row)) for row in values]

        return formatted_data

    @classmethod
    def create_columns(cls, data: dict):
        col_dtypes = dict()
        for col, value in data.items():
            if isinstance(value, Iterable) and len(value) > 0:
                valid_values = list(val for val in value if val is not None)

                if not valid_values:
                    raise ValueError(f"Was not able to determine the dtype for column {col}. Values below:\n{value}")

                dtype = type(valid_values[0])
            else:
                raise ValueError(f"Column '{col}' is empty or not iterable. Defaulting to 'NoneType'")

            psql_dtype = PythonToPostgresDtype.convert(dtype)
            psql_log.info(f"Raw dtype {dtype} converted to PSQL dtype {psql_dtype}")
            col_dtypes[col] = psql_dtype

        return col_dtypes
    
    @classmethod
    def validate(cls, data: dict):
        col_vtypes = {col: type(v) for col, v in data.items()}
        if not all(isinstance(v, list) for v in data.values()):
            raise TypeError(f"Expected only lists for dict value types. Got:\n{col_vtypes}")

        col_lengths = {col: len(v) for col, v in data.items()}
        unique_lengths = set(col_lengths.values())
        if len(unique_lengths) > 1:
            raise ValueError(f"All lists should be the same length. List lengths:\n{col_lengths}")

    def fetch_column(self, column: str):
        return self.columns[column.lower()]

class PostgresInterface:

    def __init__(self,
                 skip_sql: bool = False):
        self.client = PostgresClient()

        self._skip_sql = skip_sql

    def insert_data(self, table_name: str, data: dict):
        if self._skip_sql:
            return

        if not data:
            return

        insertable_data = PostgresInsertableData(data)

        table_column_names = set(self.client.column_names(table_name))
        data_column_names = set(data.keys())

        missing_column_names = table_column_names - data_column_names
        if missing_column_names:
            missing_columns = [insertable_data.fetch_column(col) for col in missing_column_names]
            self.client.add_columns(table_name=table_name,
                                    columns=missing_columns)

        self.client.insert_data(table_name=table_name,
                                data=insertable_data.data)

    def fetch_data(self, table_name: str, column_names: list[str] | None = None):
        return self.client.table_data(table_name=table_name,
                                      column_names=column_names)
