from enum import Enum


def generate_mod_id(atype: str,
                    mod_ids: list[str] = None,
                    mod_text: str = None):
    if mod_ids and len(mod_ids) == 1:
        return mod_ids[0]

    if not mod_ids:
        mod_ids = ''
    if not mod_text:
        mod_text = ''

    return f"{atype}_{'_'.join(mod_ids)}_{'_'.join(mod_text)}"


class ModClass(Enum):
    IMPLICIT = 'implicitMods'
    ENCHANT = 'enchantMods'
    EXPLICIT = 'explicitMods'
    FRACTURED = 'fracturedMods'
    RUNE = 'runeMods'


class ModAffixType(Enum):
    PREFIX = 'prefix'
    SUFFIX = 'suffix'

