from enum import Enum

from src.market_item_analysis.shared.enums.item_enums import EquipmentCategory
from src.market_item_analysis.shared.enums.trade_enums import TradeCategory


class WhichCategoryType(Enum):
    Equipment = 'equipment'
    TRADE = 'trade'


class EquipmentCategoryGroups:

    category_to_trade_map = {
        EquipmentCategory.ONE_HANDED_MACE: TradeCategory.ONE_HANDED_MACE,
        EquipmentCategory.SPEAR: TradeCategory.SPEAR,
        EquipmentCategory.TWO_HANDED_MACE: TradeCategory.TWO_HANDED_MACE,
        EquipmentCategory.QUARTERSTAFF: TradeCategory.QUARTERSTAFF,
        EquipmentCategory.BOW: TradeCategory.BOW,
        EquipmentCategory.CROSSBOW: TradeCategory.CROSSBOW,
        EquipmentCategory.WAND: TradeCategory.WAND,
        EquipmentCategory.SCEPTRE: TradeCategory.SCEPTRE,
        EquipmentCategory.STAFF: TradeCategory.STAFF,
        EquipmentCategory.HELMET_STR: TradeCategory.HELMET,
        EquipmentCategory.HELMET_DEX: TradeCategory.HELMET,
        EquipmentCategory.HELMET_INT: TradeCategory.HELMET,
        EquipmentCategory.HELMET_STR_DEX: TradeCategory.HELMET,
        EquipmentCategory.HELMET_STR_INT: TradeCategory.HELMET,
        EquipmentCategory.HELMET_DEX_INT: TradeCategory.HELMET,
        EquipmentCategory.BODY_ARMOUR_STR: TradeCategory.BODY_ARMOUR,
        EquipmentCategory.BODY_ARMOUR_DEX: TradeCategory.BODY_ARMOUR,
        EquipmentCategory.BODY_ARMOUR_INT: TradeCategory.BODY_ARMOUR,
        EquipmentCategory.BODY_ARMOUR_STR_DEX: TradeCategory.BODY_ARMOUR,
        EquipmentCategory.BODY_ARMOUR_STR_INT: TradeCategory.BODY_ARMOUR,
        EquipmentCategory.BODY_ARMOUR_DEX_INT: TradeCategory.BODY_ARMOUR,
        EquipmentCategory.BODY_ARMOUR_STR_DEX_INT: TradeCategory.BODY_ARMOUR,
        EquipmentCategory.GLOVE_STR: TradeCategory.GLOVES,
        EquipmentCategory.GLOVE_DEX: TradeCategory.GLOVES,
        EquipmentCategory.GLOVE_INT: TradeCategory.GLOVES,
        EquipmentCategory.GLOVE_STR_DEX: TradeCategory.GLOVES,
        EquipmentCategory.GLOVE_STR_INT: TradeCategory.GLOVES,
        EquipmentCategory.GLOVE_DEX_INT: TradeCategory.GLOVES,
        EquipmentCategory.BOOT_STR: TradeCategory.BOOTS,
        EquipmentCategory.BOOT_DEX: TradeCategory.BOOTS,
        EquipmentCategory.BOOT_INT: TradeCategory.BOOTS,
        EquipmentCategory.BOOT_STR_DEX: TradeCategory.BOOTS,
        EquipmentCategory.BOOT_STR_INT: TradeCategory.BOOTS,
        EquipmentCategory.BOOT_DEX_INT: TradeCategory.BOOTS,
        EquipmentCategory.SHIELD_STR: TradeCategory.SHIELD,
        EquipmentCategory.BUCKLER: TradeCategory.SHIELD,
        EquipmentCategory.SHIELD_STR_DEX: TradeCategory.SHIELD,
        EquipmentCategory.SHIELD_STR_INT: TradeCategory.SHIELD,
        EquipmentCategory.FOCUS: TradeCategory.FOCUS,
        EquipmentCategory.QUIVER: TradeCategory.QUIVER,
        EquipmentCategory.LIFE_FLASK: TradeCategory.LIFE_FLASK,
        EquipmentCategory.MANA_FLASK: TradeCategory.MANA_FLASK,
    }

    _trade_to_category_map = dict()
    for category, trade_category in category_to_trade_map.items():
        if trade_category not in _trade_to_category_map:
            _trade_to_category_map[trade_category] = []

        _trade_to_category_map[trade_category].append(category)

    _socketable_trade_categories = [
        TradeCategory.ONE_HANDED_MACE,
        TradeCategory.SPEAR,
        TradeCategory.TWO_HANDED_MACE,
        TradeCategory.QUARTERSTAFF,
        TradeCategory.BOW,
        TradeCategory.CROSSBOW,
        TradeCategory.WAND,
        TradeCategory.SCEPTRE,
        TradeCategory.STAFF,
        TradeCategory.HELMET,
        TradeCategory.BODY_ARMOUR,
        TradeCategory.GLOVES,
        TradeCategory.BOOTS,
        TradeCategory.SHIELD,
        TradeCategory.FOCUS,
    ]

    _martial_weapon_trade_categories = [
        TradeCategory.ONE_HANDED_MACE,
        TradeCategory.SPEAR,
        TradeCategory.TWO_HANDED_MACE,
        TradeCategory.QUARTERSTAFF,
        TradeCategory.BOW,
        TradeCategory.CROSSBOW,
    ]

    _non_martial_weapon_trade_categories = [
        TradeCategory.WAND,
        TradeCategory.SCEPTRE,
        TradeCategory.STAFF,
    ]

    _armour_trade_categories = [
        TradeCategory.HELMET,
        TradeCategory.BODY_ARMOUR,
        TradeCategory.GLOVES,
        TradeCategory.BOOTS,
        TradeCategory.QUIVER,
        TradeCategory.SHIELD,
        TradeCategory.FOCUS,
    ]

    _flask_trade_categories = [
        TradeCategory.LIFE_FLASK,
        TradeCategory.MANA_FLASK,
    ]

    @classmethod
    def _fetch_categories(cls, which: WhichCategoryType, trade_categories: list):
        if which == WhichCategoryType.TRADE:
            return trade_categories

        return [
            category
            for trade_category in trade_categories
            for category in cls._trade_to_category_map[trade_category]
        ]

    @classmethod
    def fetch_socketable_categories(cls, which: WhichCategoryType) -> list:
        return cls._fetch_categories(which=which, trade_categories=cls._socketable_trade_categories)

    @classmethod
    def fetch_martial_weapon_categories(cls, which: WhichCategoryType):
        return cls._fetch_categories(which=which, trade_categories=cls._martial_weapon_trade_categories)

    @classmethod
    def fetch_non_martial_weapon_categories(cls, which: WhichCategoryType):
        return cls._fetch_categories(which=which, trade_categories=cls._non_martial_weapon_trade_categories)

    @classmethod
    def fetch_armour_categories(cls, which: WhichCategoryType):
        return cls._fetch_categories(which=which, trade_categories=cls._armour_trade_categories)

    @classmethod
    def fetch_flask_categories(cls, which: WhichCategoryType):
        return cls._fetch_categories(which=which, trade_categories=cls._flask_trade_categories)