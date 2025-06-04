
import re
from typing import Iterable

from shared.logging import LogFile, LogsHandler, log_errors

psql_log = LogsHandler().fetch_log(log_e=LogFile.PSQL)

def python_dtype_to_postgres(dtype) -> str:
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


@log_errors(psql_log)
def determine_col_dtypes(raw_data: dict):
    col_dtypes = dict()
    for col, value in raw_data.items():
        if isinstance(value, Iterable) and len(value) > 0:
            valid_values = list(val for val in value if val is not None)

            if not valid_values:
                raise ValueError(f"Was not able to determine the dtype for column {col}. Values below:\n{value}")

            dtype = type(valid_values[0])
        else:
            raise ValueError(f"Column '{col}' is empty or not iterable. Defaulting to 'NoneType'")

        psql_dtype = python_dtype_to_postgres(dtype)
        psql_log.info(f"Raw dtype {dtype} converted to PSQL dtype {psql_dtype}")
        col_dtypes[col] = psql_dtype

    return col_dtypes


def format_data_into_rows(data: dict) -> list:
    columns = list(data.keys())
    values = zip(*data.values())

    # Build the list of dictionaries
    formatted_data = [dict(zip(columns, row)) for row in values]

    return formatted_data

@log_errors(psql_log)
def validate_dict_lists(data: dict):
    vtypes = [type(v) for v in data.values()]
    if not all(isinstance(v, list) for v in data.values()):
        raise TypeError(f"Expected only lists for dict value types. Got:\n{vtypes}")

    lengths = set(len(v) for v in data.values())
    if len(lengths) > 1:
        raise ValueError(f"All lists should be the same length. List lengths:\n{lengths}")




