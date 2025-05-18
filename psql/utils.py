import logging
import re
from typing import Iterable


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


def determine_col_dtypes(raw_data: dict):
    logging.info("Determining column dtypes")

    col_dtypes = dict()
    for col, value in raw_data.items():
        if isinstance(value, Iterable) and len(value) > 0:
            valid_val = list(val for val in value if val)[0]

            if not valid_val:
                raise ValueError(f"Was not able to determine the dtype for column {col}. Values below:\n{value}")

            dtype = type(valid_val)
        else:
            raise ValueError(f"Column '{col}' is empty or not iterable. Defaulting to 'NoneType'")

        logging.info(f"Determined new col {col} raw dtype: {dtype}")
        psql_dtype = python_dtype_to_postgres(dtype)
        logging.info(f"Determined new col {col} psql dtype: {psql_dtype}")
        col_dtypes[col] = psql_dtype

    return col_dtypes


def format_column_name(column_name: str):
    c = column_name.replace('#', 'N')
    c = c.replace('%', 'P')
    c = re.sub(r'[^a-zA-Z0-9]', '_', c)
    c = c.lower()
    c = c.replace(' ', '_')

    c = c[:63]  # Psql column names have a character limit of 63

    return c


def format_data_into_rows(data: dict) -> list:
    columns = list(data.keys())
    values = zip(*data.values())

    # Build the list of dictionaries
    formatted_data = [dict(zip(columns, row)) for row in values]

    return formatted_data


def validate_dict_lists(data: dict):
    vtypes = [type(v) for v in data.values()]
    if not all(isinstance(v, list) for v in data.values()):
        raise TypeError(f"Expected only lists for dict value types. Got:\n{vtypes}")

    lengths = set(len(v) for v in data.values())
    if len(lengths) > 1:
        raise ValueError(f"All lists should be the same length. List lengths:\n{lengths}")




