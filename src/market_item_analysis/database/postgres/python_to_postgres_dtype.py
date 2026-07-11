from typing import Iterable

psql_log = LogsHandler().fetch_log(log_e=LogFile.PSQL)


class PythonToPostgresDtype:

    @classmethod
    def convert(cls, dtype: str) -> str:
        """
        Convert a Python/numpy/pandas dtype to a PostgreSQL column type.
        """
        # Normalize dtype to string for easier checking
        dt = dtype.__name__.lower()

        if dt.startswith('int') or dt == 'int64' or dt == 'int32' or dt == 'int':
            # Default integer type in PG
            return 'INTEGER'
        elif dt.startswith('float') or dt == 'float64' or dt == 'float32' or dt == 'float':
            return 'FLOAT'
        elif dt == 'bool' or dt == 'boolean':
            return 'BOOLEAN'
        elif 'datetime' in dt:
            return 'TIMESTAMP'
        elif dt == 'object' or dt == 'string' or dt == 'str':
            # Usually pandas object dtype is string
            return 'TEXT'
        elif dt.startswith('category'):
            # Categories can be stored as TEXT or ENUM, but TEXT is simpler
            return 'TEXT'
        else:
            # Fallback
            return 'TEXT'
