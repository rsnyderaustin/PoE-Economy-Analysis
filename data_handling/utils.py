import logging
import re
from datetime import datetime, timezone

import pytz
from dateutil.parser import isoparse

from shared.item_enums import ModAffixType

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


def determine_mod_affix_type(mod_dict: dict) -> ModAffixType:
    mod_affix = None
    if mod_dict['tier']:
        first_letter = mod_dict['tier'][0]
        if first_letter == 's':
            mod_affix = ModAffixType.SUFFIX
        elif first_letter == 'p':
            mod_affix = ModAffixType.PREFIX
        else:
            raise ValueError(f"Did not recognize first character as an affix type for "
                             f"item tier {mod_dict['tier']}")

    return mod_affix


def determine_mod_tier(mod_dict: dict) -> int | None:
    mod_tier = None
    if mod_dict['tier']:
        mod_tier_match = re.search(r'\d+', mod_dict['tier'])
        if mod_tier_match:
            mod_tier = mod_tier_match.group()
        else:
            logging.error(f"Did not find a tier number for item tier {mod_dict['tier']}")
            mod_tier = None
    return int(mod_tier) if mod_tier else None


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
