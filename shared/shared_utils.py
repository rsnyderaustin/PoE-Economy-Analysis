import pprint
import re
from collections import Counter
from datetime import datetime

import pandas as pd
import pytz

import file_management
from file_management import DataPath
from .trade_enums import ItemCategory


def form_column_name(col_name: str) -> str:
    return col_name.lower().replace(' ', '_')


def _process_bracketed_text(match):
    content = match.group(1)

    if '|' in content:
        return content.split('|', 1)[1]

    return content


def remove_piped_brackets(text: str):
    result = re.sub(r'\[(.*?)\]', _process_bracketed_text, text)
    return result


def parse_values_from_text(mod_text) -> tuple:
    if isinstance(mod_text, int) or isinstance(mod_text, float):
        return (float(mod_text),)

    numbers = tuple(map(float, re.findall(r'\d+(?:\.\d+)?', mod_text)))
    return numbers


def find_duplicate_values(items: list):
    counts = Counter(items)

    duplicates = [item for item, count in counts.items() if count > 1]
    return duplicates


def sanitize_mod_text(mod_text: str):
    mod_text = re.sub(r'\d+', '#', mod_text)
    mod_text = remove_piped_brackets(mod_text)
    mod_text = mod_text.replace(' ', '_').lower()
    return mod_text


def determine_mod_ids(mod_dict: dict):
    mod_ids = [
        mod_magnitude_dict['hash']
        for mod_magnitude_dict in mod_dict['magnitudes']
    ]
    return mod_ids


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


def _apply_create_conversions_dict(row, conversions_dict: dict):
    date = datetime.strptime(row['Date'], '%Y-%m-%d')
    currency = row['Currency']
    conversion_rate = row['ExaltPerCurrency']

    if date not in conversions_dict:
        conversions_dict[date] = dict()

    conversions_dict[date][currency] = conversion_rate


class CurrencyConverter:

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(CurrencyConverter, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        if getattr(self, '_initialized', False):
            return

        files_manager = file_management.FilesManager()

        conversions_df = files_manager.file_data[DataPath.CURRENCY_CONVERSIONS]
        self.conversions_dict = dict()
        conversions_df.apply(_apply_create_conversions_dict, axis=1, args=(self.conversions_dict,))

        self._initialized = True

    def convert_to_exalts(self, currency: str, currency_amount: int | float, relevant_date: datetime):
        if currency == 'exalted':
            return currency_amount

        most_recent_date = min(self.conversions_dict.keys(), key=lambda d: abs(d - relevant_date))
        exchange_rate = self.conversions_dict[most_recent_date][currency]

        return currency_amount * exchange_rate


currency_converter = CurrencyConverter()


def log_dict(dict_, only_real_values: bool = True):
    print("\n\n")
    if only_real_values:
        dict_ = {
            col: val
            for col, val in dict_.items() if val and not pd.isna(val)
        }
    pprint.pprint(dict_)


def parse_poecd_mtypes_string(mtypes_string: str) -> list:
    if not mtypes_string:
        return []
    parsed = [part for part in mtypes_string.split('|') if part]
    return parsed


def calculate_max_quality_pdps(quality, phys_damage, attacks_per_second):
    current_multiplier = 1 + (quality / 100)
    max_multiplier = 1.20

    # Calculate the base damage and then the 20% quality damage
    base_damage = phys_damage / current_multiplier
    max_quality_damage = base_damage * max_multiplier

    max_quality_pdps = max_quality_damage * attacks_per_second

    return max_quality_pdps


def calculate_elemental_dps(cold_damage, fire_damage, lightning_damage, attacks_per_second):
    edps = (cold_damage + fire_damage + lightning_damage) * attacks_per_second
    return edps


