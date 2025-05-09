from datetime import datetime
from enum import Enum
import pytz
import re
from collections import Counter


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


def replace_mod_text_numbers(mod_text: str, replacement_values):
    replacement_values = [str(value) for value in replacement_values]

    def repl_function(match):
        return replacement_values.pop(0)

    new_string = re.sub(r'\d+', string=mod_text, repl=repl_function)
    return new_string


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


def determine_mod_values_range(mod_magnitude_dict: dict) -> tuple:
    if 'min' in mod_magnitude_dict and 'max' in mod_magnitude_dict:
        values_range = mod_magnitude_dict['min'], mod_magnitude_dict['max']
    else:
        value = next(v for k, v in mod_magnitude_dict.items() if k != 'hash')
        values_range = value, value

    return values_range


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
