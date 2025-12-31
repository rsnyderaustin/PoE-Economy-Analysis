from datetime import datetime, timezone
from enum import Enum
from typing import Iterable


def generic_to_dict(val, _depth: int = 0) -> dict:
    if _depth == 0:
        val = val.__dict__.copy()

    _depth += 1

    """Recursively convert an object to a dict, handling nested objects and iterables."""
    # Handle None
    if val is None:
        return None

    # Handle primitives (str, int, float, bool)
    if isinstance(val, (str, int, float, bool)):
        return val

    if isinstance(val, Enum):
        return val.value

    # Handle datetime objects
    if isinstance(val, datetime):
        return val.isoformat()

    # If object has a to_dict method, use it
    if hasattr(val, 'to_dict') and callable(obj.to_dict):
        return val.to_dict()

    # Handle dictionaries
    if isinstance(val, dict):
        return {key: generic_to_dict(value) for key, value in val.items()}

    # Handle lists, tuples, sets
    if isinstance(val, (list, tuple, set)):
        return [generic_to_dict(item) for item in val]

    if hasattr(val, 'to_dict') and callable(val.to_dict):
        return val.to_dict()

    # Handle objects with __dict__ (custom classes)
    if hasattr(val, '__dict__'):
        return {key: generic_to_dict(value) for key, value in val.__dict__.items()}

    # Fallback: return as-is (or raise an error if you prefer)
    return val


def format_date_into_utc(listing_date):
    if isinstance(listing_date, str):
        listing_date = listing_date.lower().replace("z", "+00:00")
        dt = datetime.fromisoformat(listing_date)
    elif isinstance(listing_date, datetime):
        dt = listing_date
    else:
        raise TypeError("Expected str or datetime.datetime")

    # Ensure it's timezone-aware in UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)

    return dt

