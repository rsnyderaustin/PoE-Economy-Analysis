from datetime import datetime, timezone
from enum import Enum

from dateutil.parser import isoparse


def generate_mod_id(atype: str,
                    mod_ids: list[str] = None):
    if mod_ids and len(mod_ids) == 1:
        return mod_ids[0]

    if not mod_ids:
        mod_ids = []

    return f"{atype}_{'_'.join(mod_ids)}"


def determine_days_since_listed(when_listed: str):
    past_time = isoparse(when_listed)
    now = datetime.now(timezone.utc)

    days_diff = (now - past_time).days
    return days_diff


class ModClass(Enum):
    IMPLICIT = 'implicitMods'
    ENCHANT = 'enchantMods'
    EXPLICIT = 'explicitMods'
    FRACTURED = 'fracturedMods'
    RUNE = 'runeMods'


class ModAffixType(Enum):
    PREFIX = 'prefix'
    SUFFIX = 'suffix'

