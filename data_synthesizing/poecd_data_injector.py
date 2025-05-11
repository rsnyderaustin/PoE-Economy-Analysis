import logging

import rapidfuzz

import file_management
from file_management import FileKey
from instances_and_definitions import ItemMod, ModClass
from poecd_api.data_management import GlobalAtypesManager
from shared import shared_utils
from . import utils


class PoecdInjector:

    def __init__(self, global_atypes_manager: GlobalAtypesManager):
        """
        This is the parent class of the whole package.
        """
        self.global_atypes_manager = global_atypes_manager
        self.mod_matcher = mod_matching.ModMatcher()

    def _should_inject(self, item_mod: ItemMod):
        """
        Implicit mods don't have weights, and we don't have weights for corruption enchantments yet
        Both also probably have mod types, but they don't matter since they can't even be rolled with essences
        """
        return item_mod.mod_class not in [ModClass.IMPLICIT, ModClass.ENCHANT]

    def inject_poecd_data_into_mod(self, item_mod: ItemMod) -> ItemMod:
        if not self._should_inject(item_mod):
            return item_mod

        poecd_mod_id = self._match_mod(item_mod)
        if not poecd_mod_id:
            logging.info(f"Parent mod:")
            shared_utils.log_dict(item_mod.__dict__)
            logging.info(f"Sub Mods:")
            for sub_mod in item_mod.sub_mods:
                shared_utils.log_dict(sub_mod.__dict__)
            raise RuntimeError(f"Could not find matching Poecd mod for Trade API mod. See above")

        atype_manager = self._poecd_data.fetch_atype_manager(item_mod.atype)
        poecd_mod = atype_manager.fetch_mod(mod_id=poecd_mod_id)

        try:
            item_mod.weighting = poecd_mod.fetch_weighting(ilvl=str(item_mod.mod_ilvl))
        except KeyError:
            logging.info("\n\n--------------- Item Mod ----------------")
            api_trade_skills = [sub_mod.sanitized_mod_text for sub_mod in item_mod.sub_mods]
            logging.info(f"Item mod: {api_trade_skills}")
            shared_utils.log_dict(item_mod.__dict__)

            logging.info("\n\n")
            logging.info("------------ Poecd Matched Mod ---------------")
            shared_utils.log_dict(f"Poecd mod: {poecd_mod.mod_text}")
            raise KeyError
        item_mod.mod_types = poecd_mod.mod_types

