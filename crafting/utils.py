from shared import ItemCategory, socketable_items


def determine_max_sockets(item_category: ItemCategory):
    if item_category not in socketable_items:
        return 0
    if item_category in [
        ItemCategory.ONE_HANDED_MACE,
        ItemCategory.SPEAR,
        ItemCategory.WAND,
        ItemCategory.SCEPTRE,
        ItemCategory.HELMET,
        ItemCategory.GLOVES,
        ItemCategory.BOOTS,
        ItemCategory.SHIELD,
        ItemCategory.FOCUS,
        ItemCategory.BUCKLER
    ]:
        return 1
    elif item_category in [
        ItemCategory.TWO_HANDED_MACE,
        ItemCategory.QUARTERSTAFF,
        ItemCategory.BOW,
        ItemCategory.CROSSBOW,
        ItemCategory.STAFF,
        ItemCategory.BODY_ARMOUR
    ]:
        return 2
    else:
        raise TypeError(f"Could not determine max sockets for item category {item_category}")
