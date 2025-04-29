
from enum import Enum


class Weapon(Enum):
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


class Armour(Enum):
    HELMET = 'helmet'
    BODY_ARMOUR = 'body armour'
    GLOVES = 'gloves'
    BOOTS = 'boots'


class OffHand(Enum):
    QUIVER = 'quiver'
    SHIELD = 'shield'
    FOCUS = 'focus'
    BUCKLER = 'buckler'


class Jewelry(Enum):
    AMULET = 'amulet'
    BELT = 'belt'
    RING = 'ring'


class Gem(Enum):
    SKILL_GEM = 'skill gem'
    SUPPORT_GEM = 'support gem'
    META_GEM = 'meta gem'


class Flask(Enum):
    LIFE_FLASK = 'life glask'
    MANA_FLASK = 'mana flask'


class Socketer(Enum):
    RUNE = 'rune'
    SOUL_CORE = 'soul core'
    TALISMAN = 'talisman'
