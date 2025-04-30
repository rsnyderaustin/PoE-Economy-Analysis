
from enum import Enum


class ModClass(Enum):
    IMPLICIT = 'implicitMods'
    ENCHANT = 'enchantMods'
    EXPLICIT = 'explicitMods'
    FRACTURED = 'fracturedMods'
    RUNE = 'runeMods'


class ModAffixType(Enum):
    PREFIX = 'prefix'
    SUFFIX = 'suffix'
