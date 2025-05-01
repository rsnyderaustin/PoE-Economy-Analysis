
from abc import ABC

from enum import Enum


class WeaponAttribute(Enum):
    ATTACKS_PER_SECOND = 'aps'
    CRIT_CHANCE = 'crit'
    DAMAGE = 'damage'
    DPS = 'dps'
    ELEMENTAL_DPS = 'edps'
    PHYSICAL_DPS = 'pdps'


class ArmourAttribute(Enum):
    ARMOUR = 'ar'
    BLOCK = 'block'
    ENERGY_SHIELD = 'es'
    EVASION = 'ev'


class MiscQueryAttribute(Enum):
    CATEGORY = 'category'
    ILVL = 'ilvl'
    QUALITY = 'quality'
    CORRUPTED = 'corrupted'
    IDENTIFIED = 'identified'
    MIRRORED = 'mirrored'
    RARITY = 'rarity'
    RUNE_SOCKETS = 'rune_sockets'
    SPIRIT = 'spirit'


class Requirement(Enum):
    LEVEL = 'lvl'
    STRENGTH = 'str'
    INTELLIGENCE = 'int'
    DEXTERITY = 'dex'


class Modifier(Enum):
    IMPLICIT = 'implicitMods'
    EXPLICIT = 'explicitMods'
    ENCHANT = 'enchantMods'
    RUNE = 'runeMods'
    FRACTURED = 'fracturedMods'


class Rarity(Enum):
    NORMAL = 'normal'
    MAGIC = 'magic'
    RARE = 'rare'
    UNIQUE = 'unique'


class Skill(Enum):
    MALICE = 'malice'


class JewelRadius(Enum):
    SMALL = 'small'
    MEDIUM = 'medium'
    LARGE = 'large'
    VERY_LARGE = 'very_large'
    MASSIVE = 'massive'


class ItemCategory(Enum):
    QUARTERSTAFF = 'weapon.warstaff'
    RUNE = 'currency.rune'
    GEM = 'gem'


class StatFilterType(Enum):
    AND = 'and'
    WEIGHTED = 'weight'
    WEIGHTED_V2 = 'weight2'
    IF_PRESENT = 'if'
    COUNT = 'count'


class MetaSearchType(Enum):
    EQUIPMENT = 'equipment_filters'
    TRADE = 'trade_filters'
    REQUIREMENT = 'req_filters'
    TYPE = 'type_filters'
    MISC = 'misc_filters'


class MiscSearchParameter(Enum):
    FILTERS = 'filters'
    STATS = 'stats'
    STATUS = 'status'
    DISABLED = 'disabled'
    OPTION = 'option'
    PRICE = 'price'
    MIN = 'min'
    MAX = 'max'
    VALUE = 'value'
    ID = 'id'
    WEIGHT = 'weight'
    TYPE = 'type'


class ListedSince(Enum):
    UP_TO_1_HOUR = '1hour'
    UP_TO_3_HOURS = '3hours'
    UP_TO_12_HOURS = '12hours'
    UP_TO_1_DAY = '1day'
    UP_TO_3_DAYS = '3days'
    UP_TO_1_WEEK = '1week'
    UP_TO_2_WEEKS = '2weeks'
    UP_TO_1_MONTH = '1month'
    UP_TO_2_MONTHS = '2months'
