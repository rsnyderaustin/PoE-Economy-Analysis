import logging
from datetime import datetime, timezone

import pytz
from dateutil.parser import isoparse

from program_logging import log_errors

_dt = datetime(2025, 4, 4, 12, 0, 0)
_pacific = pytz.timezone('US/Pacific')

league_start_date = _pacific.localize(_dt)


def determine_minutes_since(relevant_date: str | datetime, later_date: str | datetime = None) -> float:
    if isinstance(relevant_date, str):
        relevant_date = isoparse(relevant_date)

    if not later_date:
        later_date = datetime.now(timezone.utc)
    elif isinstance(later_date, str):
        later_date = isoparse(later_date)

    minutes_diff = (later_date - relevant_date).total_seconds() / 60
    return round(minutes_diff, 2)

@log_errors(logging.getLogger())
def convert_string_into_number(s):
    try:
        int_val = int(s)
        return int_val
    except ValueError:
        try:
            float_val = float(s)
            return float_val
        except ValueError:
            raise TypeError(f"String value {s} expected to represent a number, but did not.")
