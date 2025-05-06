
import logging
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


def parse_values_from_mod_text(mod_text: str) -> tuple:
    numbers = tuple(map(float, re.findall(r'\b\d+\b', mod_text)))
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
