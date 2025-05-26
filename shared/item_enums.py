from enum import Enum


class ModAffixType(Enum):
    PREFIX = 'prefix'
    SUFFIX = 'suffix'


class DerivedMod(Enum):
    MAX_QUALITY_PDPS = 'max_quality_pdps'
    FIRE_DPS = 'fire_dps'
    COLD_DPS = 'cold_dps'
    LIGHTNING_DPS = 'lightning_dps'
    ELEMENTAL_DPS = 'elemental_dps'
    CHAOS_DPS = 'chaos_dps'


class LocalMod(Enum):
    # Base Stats
    ATTACKS_PER_SECOND = 'attacks_per_second'
    PHYSICAL_DAMAGE = 'physical_damage'
    COLD_DAMAGE = 'cold_damage'
    FIRE_DAMAGE = 'fire_damage'
    LIGHTNING_DAMAGE = 'lightning_damage'
    CHAOS_DAMAGE = 'chaos_damage'
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


class ItemCategory(Enum):
    ONE_HANDED_MACE = 'one_hand_mace'
    SPEAR = 'spear'
    TWO_HANDED_MACE = 'two_hand_mace'
    QUARTERSTAFF = 'quarterstaff'
    BOW = 'bow'
    CROSSBOW = 'crossbow'
    WAND = 'wand'
    SCEPTRE = 'sceptre'
    STAFF = 'staff'
    HELMET = 'helmet'
    BODY_ARMOUR = 'body_armour'
    GLOVES = 'gloves'
    BOOTS = 'boots'
    SHIELD = 'shield'
    FOCUS = 'focus'
    BUCKLER = 'buckler'
    QUIVER = 'quiver'
    LIFE_FLASK = 'life_flask'
    MANA_FLASK = 'mana_flask'
    SKILL_GEM = 'skill_gem'
    META_GEM = 'meta_gem'
    SUPPORT_GEM = 'support_gem'
