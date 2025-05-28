from enum import Enum

from shared.enums.item_enums import ItemCategory
from shared.enums.trade_enums import TradeItemCategory


class WhichCategoryType(Enum):
    ITEM = 'item_category'
    TRADE = 'trade_category'


class ItemCategoryGroups:
    _item_to_trade_map = {
        ItemCategory.ONE_HANDED_MACE: TradeItemCategory.ONE_HANDED_MACE,
        ItemCategory.SPEAR: TradeItemCategory.SPEAR,
        ItemCategory.TWO_HANDED_MACE: TradeItemCategory.TWO_HANDED_MACE,
        ItemCategory.QUARTERSTAFF: TradeItemCategory.QUARTERSTAFF,
        ItemCategory.BOW: TradeItemCategory.BOW,
        ItemCategory.CROSSBOW: TradeItemCategory.CROSSBOW,
        ItemCategory.WAND: TradeItemCategory.WAND,
        ItemCategory.SCEPTRE: TradeItemCategory.SCEPTRE,
        ItemCategory.STAFF: TradeItemCategory.STAFF,
        ItemCategory.HELMET: TradeItemCategory.HELMET,
        ItemCategory.BODY_ARMOUR: TradeItemCategory.BODY_ARMOUR,
        ItemCategory.GLOVES: TradeItemCategory.GLOVES,
        ItemCategory.BOOTS: TradeItemCategory.BOOTS,
        ItemCategory.SHIELD: TradeItemCategory.SHIELD,
        ItemCategory.FOCUS: TradeItemCategory.FOCUS,
        ItemCategory.BUCKLER: TradeItemCategory.BUCKLER,
        ItemCategory.QUIVER: TradeItemCategory.QUIVER,
        ItemCategory.LIFE_FLASK: TradeItemCategory.LIFE_FLASK,
        ItemCategory.MANA_FLASK: TradeItemCategory.MANA_FLASK,
    }

    _trade_to_item_map = None

    _socketable_item_categories = [
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

    _martial_weapon_categories = [
        ItemCategory.ONE_HANDED_MACE,
        ItemCategory.SPEAR,
        ItemCategory.TWO_HANDED_MACE,
        ItemCategory.QUARTERSTAFF,
        ItemCategory.BOW,
        ItemCategory.CROSSBOW
    ]

    _non_martial_weapon_categories = [
        ItemCategory.WAND,
        ItemCategory.SCEPTRE,
        ItemCategory.STAFF
    ]

    _armour_categories = [
        ItemCategory.HELMET,
        ItemCategory.BODY_ARMOUR,
        ItemCategory.GLOVES,
        ItemCategory.BOOTS,
        ItemCategory.QUIVER,
        ItemCategory.SHIELD,
        ItemCategory.FOCUS,
        ItemCategory.BUCKLER
    ]

    _flask_categories = [
        ItemCategory.LIFE_FLASK,
        ItemCategory.MANA_FLASK
    ]

    @classmethod
    def _initialize_maps(cls):
        cls._trade_to_item_map = {v: k for k, v in cls._item_to_trade_map.items()}
        cls._socketable_trade_categories = [
            cls._item_to_trade_map[item] for item in cls._socketable_item_categories
        ]
        cls._martial_weapon_trade_categories = [
            cls._item_to_trade_map[item] for item in cls._martial_weapon_categories
        ]
        cls._non_martial_weapon_trade_categories = [
            cls._item_to_trade_map[item] for item in cls._non_martial_weapon_categories
        ]
        cls._armour_trade_categories = [
            cls._item_to_trade_map[item] for item in cls._armour_categories
        ]
        cls._flask_trade_categories = [
            cls._item_to_trade_map[item] for item in cls._flask_categories
        ]

    @classmethod
    def to_item_category(cls, trade_category: TradeItemCategory):
        return cls._trade_to_item_map[trade_category]

    @classmethod
    def to_trade_category(cls, item_category: ItemCategory):
        return cls._item_to_trade_map[item_category]

    @classmethod
    def fetch_socketable_item_categories(cls, which_type: WhichCategoryType = WhichCategoryType.ITEM):
        return cls._socketable_item_categories if which_type == WhichCategoryType.ITEM else cls._socketable_trade_categories

    @classmethod
    def fetch_martial_weapon_categories(cls, which_type: WhichCategoryType = WhichCategoryType.ITEM):
        return cls._martial_weapon_categories if which_type == WhichCategoryType.ITEM else cls._martial_weapon_trade_categories

    @classmethod
    def fetch_non_martial_weapon_categories(cls, which_type: WhichCategoryType = WhichCategoryType.ITEM):
        return cls._non_martial_weapon_categories if which_type == WhichCategoryType.ITEM else cls._non_martial_weapon_trade_categories

    @classmethod
    def fetch_armour_categories(cls, which_type: WhichCategoryType = WhichCategoryType.ITEM):
        return cls._armour_categories if which_type == WhichCategoryType.ITEM else cls._armour_trade_categories

    @classmethod
    def fetch_flask_categories(cls, which_type: WhichCategoryType = WhichCategoryType.ITEM):
        return cls._flask_categories if which_type == WhichCategoryType.ITEM else cls._flask_trade_categories


# Ensure mappings are initialized at module/class load time
ItemCategoryGroups._initialize_maps()
