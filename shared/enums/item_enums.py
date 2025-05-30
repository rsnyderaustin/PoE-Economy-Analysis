from enum import Enum


class ModAffixType(Enum):
    PREFIX = 'prefix'
    SUFFIX = 'suffix'


class CalculatedMod(Enum):
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


class AType(Enum):
    ONE_HANDED_MACE = 'one_hand_mace'
    SPEAR = 'spear'
    TWO_HANDED_MACE = 'two_hand_mace'
    QUARTERSTAFF = 'quarterstaff'
    BOW = 'bow'
    CROSSBOW = 'crossbow'
    WAND = 'wand'
    SCEPTRE = 'sceptre'
    STAFF = 'staff'
    HELMET_INT = 'helmet_int'
    HELMET_STR = 'helmet_str'
    HELMET_DEX = 'helmet_dex'
    HELMET_STR_INT = 'helmet_(str/int)'
    HELMET_STR_DEX = 'helmet_(str/dex)'
    HELMET_DEX_INT = 'helmet_(dex/int)'
    GLOVE_INT = 'glove_int'
    GLOVE_STR = 'glove_str'
    GLOVE_DEX = 'glove_dex'
    GLOVE_STR_INT = 'glove_(str/int)'
    GLOVE_STR_DEX = 'glove_(str/dex)'
    GLOVE_DEX_INT = 'glove_(dex/int)'
    BOOT_INT = 'boot_int'
    BOOT_STR = 'boot_str'
    BOOT_DEX = 'boot_dex'
    BOOT_STR_INT = 'boot_(str/int)'
    BOOT_STR_DEX = 'boot_(str/dex)'
    BOOT_DEX_INT = 'boot_(dex/int)'
    BODY_ARMOUR_INT = 'body_armour_int'
    BODY_ARMOUR_STR = 'body_armour_str'
    BODY_ARMOUR_DEX = 'body_armour_dex'
    BODY_ARMOUR_STR_INT = 'body_armour_(str/int)'
    BODY_ARMOUR_STR_DEX = 'body_armour_(str/dex)'
    BODY_ARMOUR_DEX_INT = 'body_armour_(dex/int)'
    BODY_ARMOUR_STR_DEX_INT = 'body_armour_(str/dex/int)'
    SHIELD_STR = 'shield_str'
    BUCKLER = 'buckler_dex'
    SHIELD_STR_DEX = 'shield_(str/dex)'
    SHIELD_STR_INT = 'shield_(str/int)'
    FOCUS = 'focus'
    QUIVER = 'quiver'
    LIFE_FLASK = 'life_flask'
    MANA_FLASK = 'mana_flask'
    SKILL_GEM = 'skill_gem'
    META_GEM = 'meta_gem'
    SUPPORT_GEM = 'support_gem'
    RUBY = 'ruby'
    EMERALD = 'emerald'
    SAPPHIRE = 'sapphire'
    AMULET = 'amulet'
    RING = 'ring'
    BELT = 'belt'

