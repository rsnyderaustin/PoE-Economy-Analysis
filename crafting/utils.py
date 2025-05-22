
from shared import trade_item_enums


def determine_max_sockets(item_category: trade_item_enums.ItemCategory):
    if item_category not in trade_item_enums.socketable_item_categories:
        return 0
    if item_category in [
        trade_item_enums.ItemCategory.ONE_HANDED_MACE,
        trade_item_enums.ItemCategory.SPEAR,
        trade_item_enums.ItemCategory.WAND,
        trade_item_enums.ItemCategory.SCEPTRE,
        trade_item_enums.ItemCategory.HELMET,
        trade_item_enums.ItemCategory.GLOVES,
        trade_item_enums.ItemCategory.BOOTS,
        trade_item_enums.ItemCategory.SHIELD,
        trade_item_enums.ItemCategory.FOCUS,
        trade_item_enums.ItemCategory.BUCKLER
    ]:
        return 1
    elif item_category in [
        trade_item_enums.ItemCategory.TWO_HANDED_MACE,
        trade_item_enums.ItemCategory.QUARTERSTAFF,
        trade_item_enums.ItemCategory.BOW,
        trade_item_enums.ItemCategory.CROSSBOW,
        trade_item_enums.ItemCategory.STAFF,
        trade_item_enums.ItemCategory.BODY_ARMOUR
    ]:
        return 2
    else:
        raise TypeError(f"Could not determine max sockets for item category {item_category}")
