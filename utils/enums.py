
from enum import Enum


class Currency(Enum):
    MIRROR_OF_KALANDRA = 'mirror'
    DIVINE = 'divine'
    CHAOS_ORB = 'chaos'
    EXALTED_ORB = 'exalted'


currency_to_enum = {
    e.value: e for e in Currency
}


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


