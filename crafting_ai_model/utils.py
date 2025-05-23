
from shared import item_enums, trade_enums


def determine_max_sockets(item_category: trade_enums.ItemCategory):
    if item_category not in item_enums.socketable_item_categories:
        return 0
    if item_category in [
        trade_enums.ItemCategory.ONE_HANDED_MACE,
        trade_enums.ItemCategory.SPEAR,
        trade_enums.ItemCategory.WAND,
        trade_enums.ItemCategory.SCEPTRE,
        trade_enums.ItemCategory.HELMET,
        trade_enums.ItemCategory.GLOVES,
        trade_enums.ItemCategory.BOOTS,
        trade_enums.ItemCategory.SHIELD,
        trade_enums.ItemCategory.FOCUS,
        trade_enums.ItemCategory.BUCKLER
    ]:
        return 1
    elif item_category in [
        trade_enums.ItemCategory.TWO_HANDED_MACE,
        trade_enums.ItemCategory.QUARTERSTAFF,
        trade_enums.ItemCategory.BOW,
        trade_enums.ItemCategory.CROSSBOW,
        trade_enums.ItemCategory.STAFF,
        trade_enums.ItemCategory.BODY_ARMOUR
    ]:
        return 2
    else:
        raise TypeError(f"Could not determine max sockets for item category {item_category}")
