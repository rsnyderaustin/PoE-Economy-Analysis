import os
from datetime import datetime, timezone
from enum import Enum
from typing import Iterable

import psutil



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


def log_memory_usage(stage=""):
    process = psutil.Process(os.getpid())
    mem = process.memory_info().rss / (1024 ** 2)  # in MB
    print(f"[Memory] {stage}: {mem:.2f} MB")


