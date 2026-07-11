from datetime import datetime, timezone

import pytz
from dateutil.parser import isoparse


class TimeAnalysis:

    LEAGUE_START_DATE = pytz.timezone('US/Pacific').localize(datetime(2026, 5, 29, 12, 0, 0))

    @classmethod
    def minutes_since(cls, relevant_date: str | datetime, later_date: str | datetime = None) -> float:
        if isinstance(relevant_date, str):
            relevant_date = isoparse(relevant_date)

        if not later_date:
            later_date = datetime.now(timezone.utc)
        elif isinstance(later_date, str):
            later_date = isoparse(later_date)

        minutes_diff = (later_date - relevant_date).total_seconds() / 60
        return round(minutes_diff, 2)

    @classmethod
    def convert_to_utc(cls, listing_date: str | datetime) -> datetime:
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


