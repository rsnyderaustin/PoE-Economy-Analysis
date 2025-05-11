
from typing import Iterable
from datetime import datetime, timezone
from enum import Enum

from dateutil.parser import isoparse


class ModClass(Enum):
    IMPLICIT = 'implicitMods'
    ENCHANT = 'enchantMods'
    EXPLICIT = 'explicitMods'
    FRACTURED = 'fracturedMods'
    RUNE = 'runeMods'


class ModAffixType(Enum):
    PREFIX = 'prefix'
    SUFFIX = 'suffix'


def generate_mod_id(atype: str,
                    mod_ids: Iterable[str] = None,
                    affix_type: ModAffixType = None):
    mod_ids = sorted(mod_ids) if mod_ids else []
    if mod_ids and len(mod_ids) == 1:
        mod_id = f"{mod_ids[0]}_{affix_type.value}" if affix_type else mod_ids[0]
        return mod_id

    mod_id = f"{atype}_{affix_type.value}" if affix_type else atype
    mod_id = f"{mod_id}_{'_'.join(mod_ids)}" if mod_ids else mod_id

    return mod_id


def determine_days_since_listed(when_listed: str):
    past_time = isoparse(when_listed)
    now = datetime.now(timezone.utc)

    days_diff = (now - past_time).days
    return days_diff

