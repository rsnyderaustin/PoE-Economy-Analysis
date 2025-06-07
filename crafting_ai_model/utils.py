
from program_logging import LogsHandler, LogFile, log_errors
from shared import ATypeGroups
from shared.enums.item_enums import AType

craft_log = LogsHandler().fetch_log(LogFile.CRAFTING_MODEL)


@log_errors(craft_log)
def determine_max_sockets(item_atype: AType):
    if item_atype not in ATypeGroups.fetch_socketable_item_categories():
        return 0
    if item_category in [
        AType.ONE_HANDED_MACE,
        AType.SPEAR,
        AType.WAND,
        AType.SCEPTRE,
        AType.HELMET,
        AType.GLOVES,
        AType.BOOTS,
        AType.SHIELD,
        AType.FOCUS,
        AType.BUCKLER
    ]:
        return 1
    elif item_category in [
        AType.TWO_HANDED_MACE,
        AType.QUARTERSTAFF,
        AType.BOW,
        AType.CROSSBOW,
        AType.STAFF,
        AType.BODY_ARMOUR
    ]:
        return 2
    else:
        raise TypeError(f"Could not determine max sockets for item category {item_category}")
