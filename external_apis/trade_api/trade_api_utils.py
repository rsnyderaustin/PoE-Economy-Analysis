
from enum import Enum


class StatSearchType(Enum):
    AND = 'and'
    WEIGHTED = 'weight'
    WEIGHTED_V2 = 'weight2'
    IF_PRESENT = 'if'
    COUNT = 'count'


class MetaSearchType(Enum):
    TYPE = 'type_filters'
    EQUIPMENT = 'equipment_filters'
    REQUIREMENT = 'req_filters'
    MISC = 'misc_filters'
    TRADE = 'trade_filters'


class TypeFilters(Enum):
    ITEM_CATEGORY = 'category'
    ITEM_RARITY = 'rarity'
    ITEM_LEVEL = 'ilvl'
    ITEM_QUALITY = 'quality'


class EquipmentAttribute(Enum):
    SPIRIT = 'spirit'
    RUNE_SOCKETS = 'rune_sockets'


class WeaponAttribute(Enum):
    DAMAGE = 'damage'
    ATTACKS_PER_SECOND = 'aps'
    CRIT_CHANCE = 'crit'
    DPS = 'dps'
    PHYSICAL_DPS = 'pdps'
    ELEMENTAL_DPS = 'edps'


class ArmourAttribute(Enum):
    ARMOUR = 'ar'
    EVASION = 'ev'
    ENERGY_SHIELD = 'es'
    BLOCK = 'block'


class RequirementFilters(Enum):
    LEVEL = 'lvl'
    STRENGTH = 'str'
    DEXTERITY = 'dex'
    INTELLIGENCE = 'int'


class MiscFilters(Enum):
    IDENTIFIED = 'identified'
    CORRUPTED = 'corrupted'
    MIRRORED = 'mirrored'


class TradeFilters(Enum):
    LISTED = 'indexed'
    PRICE = 'price'


filter_enum_to_meta_search_type = {
    **{
        e: 'type_filters'
        for e in TypeFilters
    },
    **{
        e: 'equipment_filters'
        for e in EquipmentAttribute
    },
    **{
        e: 'req_filters'
        for e in RequirementFilters
    },
    **{
        e: 'misc_filters'
        for e in MiscFilters
    },
    **{
        e: 'trade_filters'
        for e in TradeFilters
    }
}


class ModifierClass(Enum):
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
    ANY_ARMOUR = 'armour'
    ANY_WEAPON = 'weapon'
    ANY_ONE_HANDED_MELEE_WEAPON = 'weapon.onemelee'
    ANY_TWO_HANDED_MELEE_WEAPON = 'weapon.twomelee'

    UNARMED = 'weapon.unarmed'
    CLAW = 'weapon.claw'
    DAGGER = 'weapon.dagger'
    ONE_HANDED_SWORD = 'weapon.onesword'
    ONE_HANDED_AXE = 'weapon.oneaxe'
    ONE_HANDED_MACE = 'weapon.onemace'
    SPEAR = 'weapon.spear'
    FLAIL = 'weapon.flail'

    TWO_HANDED_SWORD = 'weapon.twosword'
    TWO_HANDED_AXE = 'weapon.twoaxe'
    TWO_HANDED_MACE = 'weapon.twomace'
    QUARTERSTAFF = 'weapon.warstaff'
    ANY_RANGED_WEAPON = 'weapon.ranged'
    BOW = 'weapon.bow'
    CROSSBOW = 'weapon.crossbow'
    ANY_CASTER_WEAPON = 'weapon.caster'
    WAND = 'weapon.wand'
    SCEPTRE = 'weapon.sceptre'
    STAFF = 'weapon.staff'

    HELMET = 'armour.helmet'
    BODY_ARMOUR = 'armour.chest'
    GLOVES = 'armour.gloves'
    BOOTS = 'armour.boots'
    QUIVER = 'armour.quiver'
    SHIELD = 'armour.shield'
    FOCUS = 'armour.focus'
    BUCKLER = 'armour.buckler'

    ANY_ACCESSORY = 'accessory'
    AMULET = 'accessory.amulet'
    BELT = 'accessory.belt'
    RING = 'accessory.ring'

    ANY_GEM = 'gem'
    SKILL_GEM = 'gem.activegem'
    SUPPORT_GEM = 'gem.supportgem'
    META_GEM = 'gem.metagem'

    ANY_JEWEL = 'jewel'

    ANY_FLASK = 'flask'
    LIFE_FLASK = 'flask.life'
    MANA_FLASK = 'flask.mana'

    WAYSTONE = 'map.waystone'
    MAP_FRAGMENT = 'map.waystone'

    SOCKETABLE = 'currency.socketable'
    RUNE = 'currency.rune'
    SOUL_CORE = 'currency.soulcore'
    TALISMAN = 'currency.talisman'


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


class Currency(Enum):
    TRANSMUTATION_SHARD = "transmutation-shard"
    CHANCE_SHARD = "chance-shard"
    REGAL_SHARD = "regal-shard"
    ARTIFICERS_SHARD = "artificers-shard"
    SCROLL_OF_WISDOM = "wisdom"
    ORB_OF_TRANSMUTATION = "transmute"
    ORB_OF_AUGMENTATION = "aug"
    ORB_OF_CHANCE = "chance"
    ORB_OF_ALCHEMY = "alch"
    CHAOS_ORB = "chaos"
    VAAL_ORB = "vaal"
    REGAL_ORB = "regal"
    EXALTED_ORB = "exalted"
    DIVINE_ORB = "divine"
    ORB_OF_ANNULMENT = "annul"
    ARTIFICERS_ORB = "artificers"
    FRACTURING_ORB = "fracturing-orb"
    MIRROR_OF_KALANDRA = "mirror"
    ARMOURERS_SCRAP = "scrap"
    BLACKSMITHS_WHETSTONE = "whetstone"
    ARCANISTS_ETCHER = "etcher"
    GLASSBLOWERS_BAUBLE = "bauble"
    GEMCUTTERS_PRISM = "gcp"


socketable_items = [
    ItemCategory.ONE_HANDED_MACE,
    ItemCategory.SPEAR,
    ItemCategory.TWO_HANDED_MACE,
    ItemCategory.QUARTERSTAFF,
    ItemCategory.BOW,
    ItemCategory.CROSSBOW,
    ItemCategory.WAND,
    ItemCategory.SCEPTRE,
    ItemCategory.STAFF,
    ItemCategory.HELMET,
    ItemCategory.BODY_ARMOUR,
    ItemCategory.GLOVES,
    ItemCategory.BOOTS,
    ItemCategory.QUIVER,
    ItemCategory.SHIELD,
    ItemCategory.FOCUS,
    ItemCategory.BUCKLER
]

martial_weapons = [
    ItemCategory.ONE_HANDED_MACE,
    ItemCategory.SPEAR,
    ItemCategory.TWO_HANDED_MACE,
    ItemCategory.QUARTERSTAFF,
    ItemCategory.BOW,
    ItemCategory.CROSSBOW
]

non_martial_weapons = [
    ItemCategory.WAND,
    ItemCategory.SCEPTRE,
    ItemCategory.STAFF
]

armour = [
    ItemCategory.HELMET,
    ItemCategory.BODY_ARMOUR,
    ItemCategory.GLOVES,
    ItemCategory.BOOTS,
    ItemCategory.QUIVER,
    ItemCategory.SHIELD,
    ItemCategory.FOCUS,
    ItemCategory.BUCKLER
]

