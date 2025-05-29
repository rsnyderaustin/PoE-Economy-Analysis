from enum import Enum

from shared.enums.item_enums import AType
from shared.enums.trade_enums import TradeItemCategory


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

    _trade_to_item_map = dict()
    for atype, trade_category in atype_to_trade_map.items():
        if trade_category not in _trade_to_item_map:
            _trade_to_item_map[trade_category] = []

        _trade_to_item_map[trade_category].append(atype)

    socketable_atypes = (
        _trade_to_item_map[TradeItemCategory.ONE_HANDED_MACE] +
        _trade_to_item_map[TradeItemCategory.SPEAR] +
        _trade_to_item_map[TradeItemCategory.TWO_HANDED_MACE] +
        _trade_to_item_map[TradeItemCategory.QUARTERSTAFF] +
        _trade_to_item_map[TradeItemCategory.BOW] +
        _trade_to_item_map[TradeItemCategory.CROSSBOW] +
        _trade_to_item_map[TradeItemCategory.WAND] +
        _trade_to_item_map[TradeItemCategory.SCEPTRE] +
        _trade_to_item_map[TradeItemCategory.STAFF] +
        _trade_to_item_map[TradeItemCategory.HELMET] +
        _trade_to_item_map[TradeItemCategory.BODY_ARMOUR] +
        _trade_to_item_map[TradeItemCategory.GLOVES] +
        _trade_to_item_map[TradeItemCategory.BOOTS] +
        _trade_to_item_map[TradeItemCategory.SHIELD] +
        _trade_to_item_map[TradeItemCategory.FOCUS]
    )

    martial_weapon_atypes = (
        _trade_to_item_map[TradeItemCategory.ONE_HANDED_MACE] +
        _trade_to_item_map[TradeItemCategory.SPEAR] +
        _trade_to_item_map[TradeItemCategory.TWO_HANDED_MACE] +
        _trade_to_item_map[TradeItemCategory.QUARTERSTAFF] +
        _trade_to_item_map[TradeItemCategory.BOW] +
        _trade_to_item_map[TradeItemCategory.CROSSBOW]
    )

    non_martial_weapon_atypes = (
        _trade_to_item_map[TradeItemCategory.WAND] +
        _trade_to_item_map[TradeItemCategory.SCEPTRE] +
        _trade_to_item_map[TradeItemCategory.STAFF]
    )

    armour_atypes = (
        _trade_to_item_map[TradeItemCategory.HELMET] +
        _trade_to_item_map[TradeItemCategory.BODY_ARMOUR] +
        _trade_to_item_map[TradeItemCategory.GLOVES] +
        _trade_to_item_map[TradeItemCategory.BOOTS] +
        _trade_to_item_map[TradeItemCategory.QUIVER] +
        _trade_to_item_map[TradeItemCategory.SHIELD] +
        _trade_to_item_map[TradeItemCategory.FOCUS]
    )

    flask_atypes = (
        _trade_to_item_map[TradeItemCategory.LIFE_FLASK] +
        _trade_to_item_map[TradeItemCategory.MANA_FLASK]
    )
