import logging
import re
from datetime import datetime, timezone

import pytz
from dateutil.parser import isoparse

from instances_and_definitions import ModClass, ModAffixType
from shared import shared_utils

mod_class_to_abbrev = {
    'implicitMods': 'implicit',
    'enchantMods': 'enchant',
    'explicitMods': 'explicit',
    'fracturedMods': 'fractured',
    'runeMods': 'rune'
}


_dt = datetime(2025, 4, 4, 12, 0, 0)
_pacific = pytz.timezone('US/Pacific')

league_start_date = _pacific.localize(_dt)


def determine_mod_id_to_mod_text(mod_class: ModClass, item_data: dict, sanitize_text: bool = False) -> dict:
    abbrev_class = mod_class_to_abbrev[mod_class]

    if abbrev_class not in item_data['extended']['hashes']:
        return dict()

    hashes_list = item_data['extended']['hashes'][abbrev_class]

    mod_id_display_order = [mod_hash[0] for mod_hash in hashes_list]
    mod_text_display_order = item_data[mod_class]

    mod_id_to_text = {
        mod_id: mod_text
        for mod_id, mod_text in list(zip(mod_id_display_order, mod_text_display_order))
    }
    if sanitize_text:
        return {
            mod_id: shared_utils.sanitize_mod_text(mod_text) for mod_id, mod_text in mod_id_to_text.items()
        }

    return mod_id_to_text


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
        if first_letter == 'S':
            mod_affix = ModAffixType.SUFFIX
        elif first_letter == 'P':
            mod_affix = ModAffixType.PREFIX
        else:
            raise ValueError(f"Did not recognize first character as an affix type for "
                             f"item tier {mod_dict['tier']}")

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


