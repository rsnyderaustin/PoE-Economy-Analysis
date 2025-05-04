

import logging
import re


def _process_bracketed_text(match):
    content = match.group(1)

    if '|' in content:
        return content.split('|', 1)[1]

    return content


def remove_piped_brackets(text: str):
    result = re.sub(r'\[(.*?)\]', _process_bracketed_text, text)
    if text != result:
        logging.info(f"Converted {text} to {result}.")
    return result


def parse_values_from_mod_text(mod_text: str) -> tuple:
    numbers = tuple(map(int, re.findall(r'\b\d+\b', mod_text)))
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
    mod_text = helper_funcs.remove_piped_brackets(mod_text)
    return mod_text


def determine_mod_affix_type(mod_dict: dict):
    mod_affix = None
    if mod_dict['tier']:
        first_letter = mod_dict['tier'][0]
        if first_letter == 'S':
            mod_affix = ModAffixType.SUFFIX
        elif first_letter == 'P':
            mod_affix = ModAffixType.PREFIX
        else:
            logging.error(f"Did not recognize first character as an affix type for "
                          f"item tier {mod_dict['tier']}")
            mod_affix = None

    return mod_affix


def determine_mod_tier(mod_dict: dict) -> int:
    mod_tier = None
    if mod_dict['tier']:
        mod_tier_match = re.search(r'\d+', mod_dict['tier'])
        if mod_tier_match:
            mod_tier = mod_tier_match.group()
        else:
            logging.error(f"Did not find a tier number for item tier {mod_dict['tier']}")
            mod_tier = None
    return int(mod_tier) if mod_tier else None


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
