from typing import Iterable
import re


def python_dtype_to_postgres(dtype) -> str:
    """
    Convert a Python/numpy/pandas dtype to a PostgreSQL column type.
    """
    # Normalize dtype to string for easier checking
    dt = str(dtype).lower()

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


def determine_col_dtypes(raw_data: dict, col_names: list[str]):
    cols_data = {col: val for col, val in raw_data.items() if col in col_names}

    col_dtypes = dict()
    for col, value in cols_data.items():
        if isinstance(value, Iterable):
            dtype = type(next(iter(value)))
        else:
            dtype = type(value)

        col_dtypes[col] = python_dtype_to_postgres(dtype)

    return col_dtypes


def format_column_name(column_name: str):
    c = column_name.replace('#', 'N')
    c = c.replace('%', 'P')
    c = re.sub(r'[^a-zA-Z0-9]', '_', c)
    return c

