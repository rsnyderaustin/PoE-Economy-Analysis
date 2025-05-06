from enum import Enum


def generate_mod_id(atype: str,
                    mod_ids: list[str] = None):
    if mod_ids and len(mod_ids) == 1:
        return mod_ids[0]

    if not mod_ids:
        mod_ids = []

    return f"{atype}_{'_'.join(mod_ids)}"


class ModClass(Enum):
    IMPLICIT = 'implicitMods'
    ENCHANT = 'enchantMods'
    EXPLICIT = 'explicitMods'
    FRACTURED = 'fracturedMods'
    RUNE = 'runeMods'


class ModAffixType(Enum):
    PREFIX = 'prefix'
    SUFFIX = 'suffix'

