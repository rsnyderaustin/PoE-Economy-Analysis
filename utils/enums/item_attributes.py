
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

class MiscAttribute(Enum):
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
