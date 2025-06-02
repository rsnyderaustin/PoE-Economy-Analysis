import logging
import re
from datetime import datetime, date
from typing import Iterable
from zoneinfo import ZoneInfo

from file_management import CurrencyConversionsFile
from shared.enums.trade_enums import Currency


def extract_average_from_text(text) -> float:
    values = extract_values_from_text(text)

    values = [sum(value) / len(value) if isinstance(value, Iterable) else value for value in values]
    avg_value = sum(values) / len(values)

    return avg_value


def extract_values_from_text(text) -> list:
    matches = re.findall(r'-?\d+(?:\.\d+)?(?:\s*[–-]\s*-?\d+(?:\.\d+)?)?', text)
    result = []
    for match in matches:
        clean = re.sub(r'[–—−-]', '-', match).strip()

        if '-' in clean[1:]:  # if there's a dash not at the start, it's a range
            left_str, right_str = clean.split('-', 1)
            left = float(left_str) if '.' in left_str else int(left_str)
            right = float(right_str) if '.' in right_str else int(right_str)
            result.append((left, right))
        else:
            val = float(clean) if '.' in clean else int(clean)
            result.append(val)
    return result


def _extract_from_brackets(match):
    parts = match.group(1).split('|')
    return parts[-1] if len(parts) > 1 else parts[0]


def sanitize_text(text: str):
    brackets_pattern = r'\[(.*?)\]'
    result = re.sub(brackets_pattern, _extract_from_brackets, text)
    result = result.strip().lower().replace(' ', '_')
    return result


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
    # Replace any #-# with #_to_#
    mod_text = mod_text.strip().lower()
    result = re.sub(
        r'(-?\d+(?:\.\d+)?)\s*[–—−-]\s*(-?\d+(?:\.\d+)?)',
        r'\1_to_\2',
        mod_text
    )
    result = re.sub(r'\d+', '#', result)

    result = result.replace('.#', '').replace('+', '').replace('-', '')
    result = result.replace('#', 'n').replace('%', 'p')

    brackets_pattern = r'\[(.*?)\]'
    result = re.sub(brackets_pattern, _extract_from_brackets, result)

    result = result.replace(' ', '_').replace('__', '_')
    return result


class CurrencyConverter:
    _instance = None
    _initialized = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CurrencyConverter, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        conversions_df = CurrencyConversionsFile().load()

        self.conversions_dict = dict()
        conversions_df.apply(self._apply_create_conversions_dict, axis=1, args=(self.conversions_dict,))

    @staticmethod
    def _apply_create_conversions_dict(row, conversions_dict: dict):
        # All manual currency price documentation is done in CST
        observation_date = datetime.strptime(row['date'], '%Y-%m-%d').replace(tzinfo=ZoneInfo('America/Chicago'))
        currency = row['currency']
        conversion_rate = row['div_per_currency']

        if observation_date not in conversions_dict:
            conversions_dict[observation_date] = dict()

        conversions_dict[observation_date][currency] = conversion_rate

    def convert_to_divs(self, currency: Currency, currency_amount: int | float, relevant_date: date):
        if currency == Currency.DIVINE_ORB:
            return currency_amount

        closest_date = min(self.conversions_dict.keys(), key=lambda d: abs(d - relevant_date))

        days_between = (closest_date - relevant_date).days
        if days_between >= 3:
            logging.error(f"Date between relevant date and closest currency price observation dates in "
                          f"CurrencyConverter.convert_to_divs is {days_between}.")

        exchange_rate = self.conversions_dict[closest_date][currency.value]
        converted_amount = currency_amount * exchange_rate
        return converted_amount
