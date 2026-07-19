from datetime import datetime
from enum import Enum
from collections import defaultdict


class DictionaryService:

    @classmethod
    def convert_to_dict(cls, val, _depth: int = 0) -> dict:
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
        if hasattr(val, 'to_dict') and callable(val.to_dict):
            return val.to_dict()

        # Handle dictionaries
        if isinstance(val, dict):
            return {key: cls.convert_to_dict(value) for key, value in val.items()}

        # Handle lists, tuples, sets
        if isinstance(val, (list, tuple, set)):
            return [cls.convert_to_dict(item) for item in val]

        # Handle objects with __dict__ (custom classes)
        if hasattr(val, '__dict__'):
            return {key: cls.convert_to_dict(value) for key, value in val.__dict__.items()}

        # Fallback: return as-is (or raise an error if you prefer)
        return val

    @classmethod
    def combine_dictionaries(cls, dicts: list[dict]) -> dict:
        # Use a defaultdict to store lists of values for each key
        combined = defaultdict(list)

        # Track all unique keys found across all dictionaries
        all_keys = set()
        for d in dicts:
            all_keys.update(d.keys())

        # Build the lists, filling with None if a key is missing
        for d in dicts:
            for key in all_keys:
                combined[key].append(d.get(key, None))

        return dict(combined)

