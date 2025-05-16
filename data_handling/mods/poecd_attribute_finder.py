from dataclasses import dataclass

from instances_and_definitions import ItemMod, ModClass
from poecd_api.data_management import GlobalAtypesManager
from . import utils, mod_matching


@dataclass
class PoecdModAttributes:
    weighting: float
    mod_types: list[str] = None


class PoecdAttributeFinder:

    def __init__(self, global_atypes_manager: GlobalAtypesManager):
        """
        This is the parent class of mods
        """
        self._global_atypes_manager = global_atypes_manager
        self._mod_matcher = mod_matching.ModMatcher(global_atypes_manager=global_atypes_manager)

    def get_poecd_mod_attributes(self, item_mod: ItemMod) -> PoecdModAttributes | None:
        """

        :param item_mod:
        :return: Mod attributes (weighting and mod types) that are not available in official PoE API
        """
        if item_mod.mod_class in [ModClass.IMPLICIT, ModClass.ENCHANT]:
            return None

        poecd_mod_id = self._mod_matcher.match_mod(item_mod)
        if not poecd_mod_id:
            utils.throw_no_match_error(item_mod)

        atype_manager = self._global_atypes_manager.fetch_atype_manager(atype_name=item_mod.atype)
        poecd_mod = atype_manager.fetch_mod_by_id(mod_id=poecd_mod_id)

        try:
            return PoecdModAttributes(weighting=poecd_mod.fetch_weighting(ilvl=str(item_mod.mod_ilvl)),
                                      mod_types=poecd_mod.mod_types)
        except (KeyError, AttributeError):
            utils.throw_unavailable_mod_error(item_mod=item_mod,
                                              poecd_mod=poecd_mod)
