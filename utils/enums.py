
import inspect
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


rarity_to_enum = {
    e.value: e for e in Rarity
}


class Skill(Enum):
    MALICE = 'malice'


class JewelRadius(Enum):
    SMALL = 'small'
    MEDIUM = 'medium'
    LARGE = 'large'
    VERY_LARGE = 'very_large'
    MASSIVE = 'massive'


class ItemType(Enum):
    CLAW = 'claw'
    DAGGER = 'dagger'
    ONE_HANDED_SWORD = 'one-handed sword'
    ONE_HANDED_AXE = 'one-handed axe'
    ONE_HANDED_MACE = 'one-handed mace'
    SPEAR = 'spear'
    FLAIL = 'flail'
    TWO_HANDED_SWORD = 'two-handed sword'
    TWO_HANDED_AXE = 'two-handed axe'
    TWO_HANDED_MACE = 'two-handed mace'
    QUARTERSTAFF = 'quarterstaff'
    BOW = 'bow'
    CROSSBOW = 'crossbow'
    WAND = 'wand'
    SCEPTRE = 'sceptre'
    STAFF = 'staff'
    FISHING_ROD = 'fishing rod'
    HELMET = 'helmet'
    BODY_ARMOUR = 'body armour'
    GLOVES = 'gloves'
    BOOTS = 'boots'
    QUIVER = 'quiver'
    SHIELD = 'shield'
    FOCUS = 'focus'
    BUCKLER = 'buckler'
    AMULET = 'amulet'
    BELT = 'belt'
    RING = 'ring'
    SKILL_GEM = 'skill gem'
    SUPPORT_GEM = 'support gem'
    META_GEM = 'meta gem'
    LIFE_FLASK = 'life glask'
    MANA_FLASK = 'mana flask'
    RUNE = 'rune'
    SOUL_CORE = 'soul core'
    TALISMAN = 'talisman'

