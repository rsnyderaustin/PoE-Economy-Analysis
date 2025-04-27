import inspect
from enum import Enum


class Currency(Enum):
    MIRROR_OF_KALANDRA = 'mirror'
    DIVINE = 'divine'
    CHAOS_ORB = 'chaos'
    EXALTED_ORB = 'exalted'


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


class ItemType:
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


ItemTypeEnums = [
    e.name
    for item_type_name, item_type_enum in inspect.getmembers(ItemType)
    if inspect.isclass(item_type_enum) and issubclass(item_type_enum, Enum)
    for e in item_type_enum
]


class ItemAttributes:
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
