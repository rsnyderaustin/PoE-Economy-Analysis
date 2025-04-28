
from enum import Enum


class ModClass(Enum):
    EXPLICIT = 'explicit'
    IMPLICIT = 'implicit'
    ENCHANT = 'encahnt'
    RUNE = 'rune'
    SKILL = 'skill'


class ModAffixType(Enum):
    PREFIX = 'prefix'
    SUFFIX = 'suffix'
