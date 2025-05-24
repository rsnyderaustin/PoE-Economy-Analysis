import pprint
import re
from collections import Counter
from datetime import datetime

import pandas as pd
import pytz

import file_management
from file_management import DataPath
from .trade_enums import ItemCategory


def extract_values_from_text(text) -> int | float | tuple | None:
    raw_numbers = re.findall(r'\d+\.\d+|\d+', text)
    if len(raw_numbers) == 0:
        return None
    elif len(raw_numbers) == 1:
        num = raw_numbers[0]
        if '.' in num:
            return float(num)
        else:
            return int(num)

    # If any number contains a '.', we treat all as float
    if any('.' in num for num in raw_numbers):
        return tuple(float(num) for num in raw_numbers)
    else:
        return tuple(int(num) for num in raw_numbers)


def _extract_from_brackets(match):
    parts = match.group(1).split('|')
    return parts[-1] if len(parts) > 1 else parts[0]


def sanitize_text(text: str):
    brackets_pattern = r'\[(.*?)\]'
    result = re.sub(brackets_pattern, _extract_from_brackets, text)
    return result.lower().replace(' ', '_')


def sanitize_dict_texts(d: dict):
    if isinstance(d, dict):
        return {k: sanitize_dict_texts(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [sanitize_dict_texts(item) for item in d]
    elif isinstance(d, str):
        return sanitize_text(d)
    else:
        return d


def sanitize_mod_text(mod_text: str):
    result = re.sub(r'\d+', '#', mod_text)

    brackets_pattern = r'\[(.*?)\]'
    result = re.sub(brackets_pattern, _extract_from_brackets, result)

    result = result.replace(' ', '_').lower()
    return result


def today_date() -> str:
    central_tz = pytz.timezone("America/Chicago")
    central_now = datetime.now(central_tz)

    # Format as MM/DD/YYYY
    formatted_date = central_now.strftime("%m-%d-%Y")
    return formatted_date


def determine_central_date(timestamp_str):
    utc_time = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%SZ")
    utc_time = utc_time.replace(tzinfo=pytz.utc)

    # Define the Central Time zone
    central_tz = pytz.timezone('US/Central')

    # Convert the UTC time to Central Time
    central_time = utc_time.astimezone(central_tz)

    # Get only the date in Central Time
    central_date = central_time.date()

    return central_date


class CurrencyConverter:
    _instance = None
    _initialized = None

    def __new__(cls):
        if not hasattr(cls, '_instance'):
            cls._instance = super(CurrencyConverter, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, '_initialized', False):
            return

        files_manager = file_management.FilesManager()

        conversions_df = files_manager.file_data[DataPath.CURRENCY_CONVERSIONS]
        self.conversions_dict = dict()
        conversions_df.apply(self._apply_create_conversions_dict, axis=1, args=(self.conversions_dict,))

        self._initialized = True

    @staticmethod
    def _apply_create_conversions_dict(row, conversions_dict: dict):
        date = datetime.strptime(row['Date'], '%Y-%m-%d')
        currency = row['Currency']
        conversion_rate = row['ExaltPerCurrency']

        if date not in conversions_dict:
            conversions_dict[date] = dict()

        conversions_dict[date][currency] = conversion_rate

    def convert_to_exalts(self, currency: str, currency_amount: int | float, relevant_date: datetime):
        if currency == 'exalted':
            return currency_amount

        most_recent_date = min(self.conversions_dict.keys(), key=lambda d: abs(d - relevant_date))
        exchange_rate = self.conversions_dict[most_recent_date][currency]

        return currency_amount * exchange_rate


def log_dict(dict_, only_real_values: bool = True):
    print("\n\n")
    if only_real_values:
        dict_ = {
            col: val
            for col, val in dict_.items() if val and not pd.isna(val)
        }
    pprint.pprint(dict_)


