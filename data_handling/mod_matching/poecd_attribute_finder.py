from instances_and_definitions import ItemMod, ModClass
from poecd_api.data_management import GlobalAtypesManager
from . import utils, mod_matching
from dataclasses import dataclass


@dataclass
class PoecdModAttributes:
    weighting: float
    mod_types: list[str] = None


class PoecdAttributeFinder:

    def __init__(self, global_atypes_manager: GlobalAtypesManager):
        """
        This is the parent class of the whole package.
        """
        self._global_atypes_manager = global_atypes_manager
        self._mod_matcher = mod_matching.ModMatcher(global_atypes_manager=global_atypes_manager)

    def _should_inject(self, item_mod: ItemMod):
        """
        Implicit mods don't have weights, and we don't have weights for corruption enchantments yet
        Both also probably have mod types, but they don't matter since they can't even be rolled with essences
        """
        return item_mod.mod_class not in [ModClass.IMPLICIT, ModClass.ENCHANT]

    def get_mod_attributes(self, item_mod: ItemMod) -> PoecdModAttributes | None:
        if not self._should_inject(item_mod):
            return None

        poecd_mod_id = self._mod_matcher.match_mod(item_mod)
        if not poecd_mod_id:
            utils.log_no_match(item_mod)

        atype_manager = self._global_atypes_manager.fetch_atype_manager(atype_name=item_mod.atype)
        poecd_mod = atype_manager.fetch_mod(mod_id=poecd_mod_id)

        try:
            return PoecdModAttributes(weighting=poecd_mod.fetch_weighting(ilvl=str(item_mod.mod_ilvl)),
                                      mod_types=poecd_mod.mod_types)
        except (KeyError, AttributeError):
            utils.log_unavailable_mod_data(item_mod=item_mod,
                                           poecd_mod=poecd_mod)

    def inject_poecd_data_into_mod(self, item_mod: ItemMod) -> ItemMod:
        if not self._should_inject(item_mod):
            return item_mod

        poecd_mod_id = self._mod_matcher.match_mod(item_mod)
        if not poecd_mod_id:
            utils.log_no_match(item_mod)

        atype_manager = self._global_atypes_manager.fetch_atype_manager(atype_name=item_mod.atype)
        poecd_mod = atype_manager.fetch_mod(mod_id=poecd_mod_id)

        try:
            item_mod.weighting = poecd_mod.fetch_weighting(ilvl=str(item_mod.mod_ilvl))
            item_mod.mod_types = poecd_mod.mod_types
        except (KeyError, AttributeError):
            utils.log_unavailable_mod_data(item_mod=item_mod,
                                           poecd_mod=poecd_mod)

