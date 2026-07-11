from enum import Enum


class AffixType(Enum):
    PREFIX = 'prefix'
    SUFFIX = 'suffix'


class EquipmentCategory(Enum):
    ONE_HANDED_MACE = ('Mace|One Hand Mace', 'weapon.onemace', True, True)
    SPEAR = ('spear', 'weapon.spear', True, True)
    TWO_HANDED_MACE = ('two_hand_mace', 'weapon.twomace', True, True)
    QUARTERSTAFF = ('quarterstaff', 'weapon.warstaff', True, True)
    BOW = ('bow', 'weapon.bow', True, True)
    CROSSBOW = ('crossbow', 'weapon.crossbow', True, True)
    WAND = ('wand', 'weapon.wand', False, True)
    SCEPTRE = ('sceptre', 'weapon.sceptre', False, True)
    STAFF = ('staff', 'weapon.staff', False, True)
    TALISMAN = ('talisman', 'weapon.talisman', False, False)

    HELMET = ('helmet', 'armour.helmet', False, True)
    GLOVE = ('glove', 'armour.gloves', False, True)
    BOOT = ('boot', 'armour.boots', False, True)
    BODY_ARMOUR = ('body_armour', 'armour.chest', False, True)
    SHIELD = ('shield', 'armour.shield', False, True)
    BUCKLER = ('buckler_dex', 'armour.buckler', False, True)
    FOCUS = ('focus', 'armour.focus', False, True)
    QUIVER = ('quiver', 'armour.quiver', False, True)

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

    def __init__(self, trade_result_id: str, trade_query_id: str, is_martial: bool, is_socketable: bool):
        self.internal_id = trade_result_id
        self.trade_id = trade_query_id

        self.is_martial = is_martial
        self.is_socketable = is_socketable

    @classmethod
    def from_trade_result_id(cls, internal_id: str):
        if not hasattr(cls, '_trade_result_id_map'):
            cls._trade_result_id_map = {member.internal_id: member for member in cls}

        return cls._trade_result_id_map.get(internal_id)

    @classmethod
    def from_trade_query_id(cls, trade_id: str):
        if not hasattr(cls, '_trade_query_id_map'):
            cls._trade_query_id_map = {member.internal_id: member for member in cls}

        return cls._trade_query_id_map.get(trade_id)

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
