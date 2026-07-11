from enum import Enum


class AffixType(Enum):
    PREFIX = 'prefix'
    SUFFIX = 'suffix'


class EquipmentCategory(Enum):
    # Format: (internal_id, trade_string, is_martial, is_socketable)

    # Weapons
    ONE_HANDED_MACE = ('one_hand_mace', 'weapon.onemace', True, True)
    SPEAR = ('spear', 'weapon.spear', True, True)
    TWO_HANDED_MACE = ('two_hand_mace', 'weapon.twomace', True, True)
    QUARTERSTAFF = ('quarterstaff', 'weapon.warstaff', True, True)
    BOW = ('bow', 'weapon.bow', True, True)
    CROSSBOW = ('crossbow', 'weapon.crossbow', True, True)
    WAND = ('wand', 'weapon.wand', False, True)
    SCEPTRE = ('sceptre', 'weapon.sceptre', False, True)
    STAFF = ('staff', 'weapon.staff', False, True)
    TALISMAN = ('talisman', 'weapon.talisman', False, False)

    # Helmets
    HELMET_INT = ('helmet_int', 'armour.helmet', False, True)
    HELMET_STR = ('helmet_str', 'armour.helmet', False, True)
    HELMET_DEX = ('helmet_dex', 'armour.helmet', False, True)
    HELMET_STR_INT = ('helmet_(str/int)', 'armour.helmet', False, True)
    HELMET_STR_DEX = ('helmet_(str/dex)', 'armour.helmet', False, True)
    HELMET_DEX_INT = ('helmet_(dex/int)', 'armour.helmet', False, True)

    # Gloves
    GLOVE_INT = ('glove_int', 'armour.gloves', False, True)
    GLOVE_STR = ('glove_str', 'armour.gloves', False, True)
    GLOVE_DEX = ('glove_dex', 'armour.gloves', False, True)
    GLOVE_STR_INT = ('glove_(str/int)', 'armour.gloves', False, True)
    GLOVE_STR_DEX = ('glove_(str/dex)', 'armour.gloves', False, True)
    GLOVE_DEX_INT = ('glove_(dex/int)', 'armour.gloves', False, True)

    # Boots
    BOOT_INT = ('boot_int', 'armour.boots', False, True)
    BOOT_STR = ('boot_str', 'armour.boots', False, True)
    BOOT_DEX = ('boot_dex', 'armour.boots', False, True)
    BOOT_STR_INT = ('boot_(str/int)', 'armour.boots', False, True)
    BOOT_STR_DEX = ('boot_(str/dex)', 'armour.boots', False, True)
    BOOT_DEX_INT = ('boot_(dex/int)', 'armour.boots', False, True)

    # Body Armour
    BODY_ARMOUR_INT = ('body_armour_int', 'armour.chest', False, True)
    BODY_ARMOUR_STR = ('body_armour_str', 'armour.chest', False, True)
    BODY_ARMOUR_DEX = ('body_armour_dex', 'armour.chest', False, True)
    BODY_ARMOUR_STR_INT = ('body_armour_(str/int)', 'armour.chest', False, True)
    BODY_ARMOUR_STR_DEX = ('body_armour_(str/dex)', 'armour.chest', False, True)
    BODY_ARMOUR_DEX_INT = ('body_armour_(dex/int)', 'armour.chest', False, True)
    BODY_ARMOUR_STR_DEX_INT = ('body_armour_(str/dex/int)', 'armour.chest', False, True)

    # Shields / Other
    SHIELD_STR = ('shield_str', 'armour.shield', False, True)
    BUCKLER = ('buckler_dex', 'armour.buckler', False, True)
    SHIELD_STR_DEX = ('shield_(str/dex)', 'armour.shield', False, True)
    SHIELD_STR_INT = ('shield_(str/int)', 'armour.shield', False, True)
    FOCUS = ('focus', 'armour.focus', False, True)
    QUIVER = ('quiver', 'armour.quiver', False, True)

    # Flasks / Gems / Accessories
    LIFE_FLASK = ('life_flask', 'flask.life', False, False)
    MANA_FLASK = ('mana_flask', 'flask.mana', False, False)
    SKILL_GEM = ('skill_gem', 'gem.activegem', False, False)
    META_GEM = ('meta_gem', 'gem.metagem', False, False)
    SUPPORT_GEM = ('support_gem', 'gem.supportgem', False, False)
    RUBY = ('ruby', 'currency.socketable', False, False)
    EMERALD = ('emerald', 'currency.socketable', False, False)
    SAPPHIRE = ('sapphire', 'currency.socketable', False, False)
    AMULET = ('amulet', 'accessory.amulet', False, False)
    RING = ('ring', 'accessory.ring', False, False)
    BELT = ('belt', 'accessory.belt', False, False)

    def __init__(self, internal_id: str, trade_id: str, is_martial: bool, is_socketable: bool):
        self.internal_id = internal_id
        self.trade_id = trade_id

        self.is_martial = is_martial
        self.is_socketable = is_socketable

    @classmethod
    def get_martial_weapons(cls, as_trade_strings: bool = False):
        items = [e for e in cls if e.is_martial]

        if as_trade_strings:
            # Just return the strings the API needs
            return [e.trade_id for e in items]

        # Return the actual Enum objects
        return items


class Rarity(Enum):
    NORMAL = 'normal'
    MAGIC = 'magic'
    RARE = 'rare'
    UNIQUE = 'unique'


class JewelRadius(Enum):
    SMALL = 'small'
    MEDIUM = 'medium'
    LARGE = 'large'
    VERY_LARGE = 'very_large'
    MASSIVE = 'massive'
