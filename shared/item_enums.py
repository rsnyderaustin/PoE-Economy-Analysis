from enum import Enum

from shared import ItemCategory


class ModAffixType(Enum):
    PREFIX = 'prefix'
    SUFFIX = 'suffix'


class Atype(Enum):


class DerivedMod(Enum):
    MAX_QUALITY_PDPS = 'max_quality_pdps'
    FIRE_DPS = 'fire_dps'
    COLD_DPS = 'cold_dps'
    LIGHTNING_DPS = 'lightning_dps'
    ELEMENTAL_DPS = 'elemental_dps'

class LocalMod(Enum):
    # Base Stats
    ATTACKS_PER_SECOND = 'attacks_per_second'
    PHYSICAL_DAMAGE = 'physical_damage'
    COLD_DAMAGE = 'cold_damage'
    FIRE_DAMAGE = 'fire_damage'
    LIGHTNING_DAMAGE = 'lightning_damage'
    QUALITY = 'quality'

    # Added Damage
    ADDS_TO_FIRE_DAMAGE = 'adds_#_to_#_fire_damage'
    ADDS_TO_COLD_DAMAGE = 'adds_#_to_#_cold_damage'
    ADDS_TO_LIGHTNING_DAMAGE = 'adds_#_to_#_lightning_damage'
    ADDS_TO_PHYSICAL_DAMAGE = 'adds_#_to_#_physical_damage'

    # Increased Stats
    INCREASED_ATTACK_SPEED = '#%_increased_attack_speed'
    INCREASED_PHYSICAL_DAMAGE = '#%_increased_physical_damage'

    # Critical Hit Chance
    CRIT_CHANCE = 'critical_hit_chance'


socketable_item_categories = [
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
    ItemCategory.SHIELD,
    ItemCategory.FOCUS,
    ItemCategory.BUCKLER
]

martial_weapon_categories = [
    ItemCategory.ONE_HANDED_MACE,
    ItemCategory.SPEAR,
    ItemCategory.TWO_HANDED_MACE,
    ItemCategory.QUARTERSTAFF,
    ItemCategory.BOW,
    ItemCategory.CROSSBOW
]

non_martial_weapon_categories = [
    ItemCategory.WAND,
    ItemCategory.SCEPTRE,
    ItemCategory.STAFF
]

armour_categories = [
    ItemCategory.HELMET,
    ItemCategory.BODY_ARMOUR,
    ItemCategory.GLOVES,
    ItemCategory.BOOTS,
    ItemCategory.QUIVER,
    ItemCategory.SHIELD,
    ItemCategory.FOCUS,
    ItemCategory.BUCKLER
]


flask_categories = [
    ItemCategory.LIFE_FLASK,
    ItemCategory.MANA_FLASK
]
