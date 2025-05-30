from enum import Enum

from shared.enums.item_enums import AType
from shared.enums.trade_enums import TradeItemCategory


class WhichCategoryType(Enum):
    ATYPE = 'atype'
    TRADE = 'trade'


class ItemEnumGroups:

    atype_to_trade_map = {
        AType.ONE_HANDED_MACE: TradeItemCategory.ONE_HANDED_MACE,
        AType.SPEAR: TradeItemCategory.SPEAR,
        AType.TWO_HANDED_MACE: TradeItemCategory.TWO_HANDED_MACE,
        AType.QUARTERSTAFF: TradeItemCategory.QUARTERSTAFF,
        AType.BOW: TradeItemCategory.BOW,
        AType.CROSSBOW: TradeItemCategory.CROSSBOW,
        AType.WAND: TradeItemCategory.WAND,
        AType.SCEPTRE: TradeItemCategory.SCEPTRE,
        AType.STAFF: TradeItemCategory.STAFF,
        AType.HELMET_STR: TradeItemCategory.HELMET,
        AType.HELMET_DEX: TradeItemCategory.HELMET,
        AType.HELMET_INT: TradeItemCategory.HELMET,
        AType.HELMET_STR_DEX: TradeItemCategory.HELMET,
        AType.HELMET_STR_INT: TradeItemCategory.HELMET,
        AType.HELMET_DEX_INT: TradeItemCategory.HELMET,
        AType.BODY_ARMOUR_STR: TradeItemCategory.BODY_ARMOUR,
        AType.BODY_ARMOUR_DEX: TradeItemCategory.BODY_ARMOUR,
        AType.BODY_ARMOUR_INT: TradeItemCategory.BODY_ARMOUR,
        AType.BODY_ARMOUR_STR_DEX: TradeItemCategory.BODY_ARMOUR,
        AType.BODY_ARMOUR_STR_INT: TradeItemCategory.BODY_ARMOUR,
        AType.BODY_ARMOUR_DEX_INT: TradeItemCategory.BODY_ARMOUR,
        AType.BODY_ARMOUR_STR_DEX_INT: TradeItemCategory.BODY_ARMOUR,
        AType.GLOVE_STR: TradeItemCategory.GLOVES,
        AType.GLOVE_DEX: TradeItemCategory.GLOVES,
        AType.GLOVE_INT: TradeItemCategory.GLOVES,
        AType.GLOVE_STR_DEX: TradeItemCategory.GLOVES,
        AType.GLOVE_STR_INT: TradeItemCategory.GLOVES,
        AType.GLOVE_DEX_INT: TradeItemCategory.GLOVES,
        AType.BOOT_STR: TradeItemCategory.BOOTS,
        AType.BOOT_DEX: TradeItemCategory.BOOTS,
        AType.BOOT_INT: TradeItemCategory.BOOTS,
        AType.BOOT_STR_DEX: TradeItemCategory.BOOTS,
        AType.BOOT_STR_INT: TradeItemCategory.BOOTS,
        AType.BOOT_DEX_INT: TradeItemCategory.BOOTS,
        AType.SHIELD_STR: TradeItemCategory.SHIELD,
        AType.BUCKLER: TradeItemCategory.SHIELD,
        AType.SHIELD_STR_DEX: TradeItemCategory.SHIELD,
        AType.SHIELD_STR_INT: TradeItemCategory.SHIELD,
        AType.FOCUS: TradeItemCategory.FOCUS,
        AType.QUIVER: TradeItemCategory.QUIVER,
        AType.LIFE_FLASK: TradeItemCategory.LIFE_FLASK,
        AType.MANA_FLASK: TradeItemCategory.MANA_FLASK,
    }

    _trade_to_atype_map = dict()
    for atype, trade_category in atype_to_trade_map.items():
        if trade_category not in _trade_to_atype_map:
            _trade_to_atype_map[trade_category] = []

        _trade_to_atype_map[trade_category].append(atype)

    _socketable_trade_categories = [
        TradeItemCategory.ONE_HANDED_MACE,
        TradeItemCategory.SPEAR,
        TradeItemCategory.TWO_HANDED_MACE,
        TradeItemCategory.QUARTERSTAFF,
        TradeItemCategory.BOW,
        TradeItemCategory.CROSSBOW,
        TradeItemCategory.WAND,
        TradeItemCategory.SCEPTRE,
        TradeItemCategory.STAFF,
        TradeItemCategory.HELMET,
        TradeItemCategory.BODY_ARMOUR,
        TradeItemCategory.GLOVES,
        TradeItemCategory.BOOTS,
        TradeItemCategory.SHIELD,
        TradeItemCategory.FOCUS,
    ]

    _martial_weapon_trade_categories = [
        TradeItemCategory.ONE_HANDED_MACE,
        TradeItemCategory.SPEAR,
        TradeItemCategory.TWO_HANDED_MACE,
        TradeItemCategory.QUARTERSTAFF,
        TradeItemCategory.BOW,
        TradeItemCategory.CROSSBOW,
    ]

    _non_martial_weapon_trade_categories = [
        TradeItemCategory.WAND,
        TradeItemCategory.SCEPTRE,
        TradeItemCategory.STAFF,
    ]

    _armour_trade_categories = [
        TradeItemCategory.HELMET,
        TradeItemCategory.BODY_ARMOUR,
        TradeItemCategory.GLOVES,
        TradeItemCategory.BOOTS,
        TradeItemCategory.QUIVER,
        TradeItemCategory.SHIELD,
        TradeItemCategory.FOCUS,
    ]

    _flask_trade_categories = [
        TradeItemCategory.LIFE_FLASK,
        TradeItemCategory.MANA_FLASK,
    ]

    @classmethod
    def _convert_to_atypes(cls, which: WhichCategoryType, trade_categories: list):
        if which == WhichCategoryType.TRADE:
            return trade_categories

        return [
            atype
            for trade_category in trade_categories
            for atype in cls._trade_to_atype_map[trade_category]
        ]

    @classmethod
    def fetch_socketables(cls, which: WhichCategoryType) -> list:
        return cls._convert_to_atypes(which=which, trade_categories=cls._socketable_trade_categories)

    @classmethod
    def fetch_martial_weapons(cls, which: WhichCategoryType):
        return cls._convert_to_atypes(which=which, trade_categories=cls._martial_weapon_trade_categories)

    @classmethod
    def fetch_non_martial_weapons(cls, which: WhichCategoryType):
        return cls._convert_to_atypes(which=which, trade_categories=cls._non_martial_weapon_trade_categories)

    @classmethod
    def fetch_armours(cls, which: WhichCategoryType):
        return cls._convert_to_atypes(which=which, trade_categories=cls._armour_trade_categories)

    @classmethod
    def fetch_flasks(cls, which: WhichCategoryType):
        return cls._convert_to_atypes(which=which, trade_categories=cls._flask_trade_categories)