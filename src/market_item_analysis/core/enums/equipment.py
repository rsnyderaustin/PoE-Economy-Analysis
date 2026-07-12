from enum import Enum

from src.market_item_analysis.core.types import Range


class AffixType(Enum):
    PREFIX = 'prefix'
    SUFFIX = 'suffix'


class ModType(Enum):
    IMPLICIT = 'implicitMods'
    EXPLICIT = 'explicitMods'
    ENCHANT = 'enchantMods'
    FRACTURED = 'fracturedMods'
    RUNE = 'runeMods'

    def __init__(self, trade_result_key: str):
        self.trade_result_key = trade_result_key


class EquipmentCategory(Enum):
    ONE_HANDED_MACE = ('Mace|One Hand Mace', 'weapon.onemace', True, True)
    SPEAR = ('spear', 'weapon.spear', True, True)
    TWO_HANDED_MACE = ('two_hand_mace', 'weapon.twomace', True, True)
    QUARTERSTAFF = ('quarterstaff', 'weapon.warstaff', True, True)
    BOW = ('bow', 'weapon.bow', True, True)
    CROSSBOW = ('Crossbow', 'weapon.crossbow', True, True)
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
        self.trade_result_id = trade_result_id
        self.trade_query_id = trade_query_id

        self.is_martial = is_martial
        self.is_socketable = is_socketable

    @classmethod
    def from_trade_result_id(cls, trade_result_id: str):
        if not hasattr(cls, '_trade_result_id_map'):
            cls._trade_result_id_map = {member.trade_result_id: member for member in cls}

        return cls._trade_result_id_map.get(trade_result_id)

    @classmethod
    def from_trade_query_id(cls, trade_query_id: str):
        if not hasattr(cls, '_trade_query_id_map'):
            cls._trade_query_id_map = {member.trade_query_id: member for member in cls}

        return cls._trade_query_id_map.get(trade_query_id)

    @classmethod
    def get_martial_weapons(cls, as_trade_strings: bool = False):
        items = [e for e in cls if e.is_martial]

        if as_trade_strings:
            # Just return the strings the API needs
            return [e.trade_id for e in items]

        # Return the actual Enum objects
        return items


class EquipmentStat(Enum):

    ARMOUR = (int, '[Armour]', 'ar')
    EVASION = (int, '[Evasion|Evasion Rating]', 'ev')
    ENERGY_SHIELD = (int, '[Energy Shield|Energy Shield]', 'es')
    SPIRIT = (int, '[Spirit]', 'spirit')
    WARD = (int, '[Ward|Runic Ward]', 'ward')

    ATTACKS_PER_SECOND = (float, 'Attacks per Second', 'aps')
    CRITICAL_CHANCE = (float, '[Critical|Critical Hit] Chance', 'crit')
    PHYSICAL_DAMAGE = (Range, '[Physical] Damage', 'damage')

    ELEMENTAL_DAMAGE = (Range, '[ElementalDamage|Elemental] Damage', None)
    LIGHTNING_DAMAGE = (Range, 'Lightning Damage', None)
    FIRE_DAMAGE = (Range, 'Fire Damage', None)
    COLD_DAMAGE = (Range, 'Cold Damage', None)

    ELEMENTAL_DAMAGE_PER_SECOND = (float, None, 'edps')
    PHYSICAL_DAMAGE_PER_SECOND = (float, None, 'pdps')
    RELOAD_TIME = (float, 'Reload Time', 'reload_time')

    def __init__(self,
                 data_type: int | float | Range,
                 trade_result_id: str | None,
                 trade_query_id: str | None):
        self.data_type = data_type
        self.trade_result_id = trade_result_id
        self.trade_query_id = trade_query_id

    @classmethod
    def from_trade_result_id(cls, trade_result_id: str):
        if not hasattr(cls, '_trade_result_id_map'):
            cls._trade_result_id_map = {member.trade_result_id: member for member in cls}

        return cls._trade_result_id_map[trade_result_id]

    @property
    def queryable(self):
        return self.trade_query_id is not None

class Rarity(Enum):
    NORMAL = 'normal'
    MAGIC = 'magic'
    RARE = 'rare'
    UNIQUE = 'unique'


class AttributeType(Enum):

    DEX = ('Dexterity|Dex')
    STR = ('Strength|Str')
    INT = ('Intelligence|Int')

    def __init__(self, trade_result_id: str):
        self.trade_result_id = trade_result_id

    @classmethod
    def from_trade_result_id(cls, trade_result_id: str):
        if not hasattr(cls, '_trade_result_id_map'):
            cls._trade_result_id_map = {member.trade_result_id: member for member in cls}

        return cls._trade_result_id_map.get(trade_result_id)


class JewelRadius(Enum):
    SMALL = 'small'
    MEDIUM = 'medium'
    LARGE = 'large'
    VERY_LARGE = 'very_large'
    MASSIVE = 'massive'
