
import logging

from data_synthesizing.things.mods.mod_tier import ModTier
from shared.enums import ModAffixType
from .atype_manager import ATypeManager


class GlobalATypesManager:

    def __init__(self):
        self._atype_to_manager = dict()

    def add_atype_manager(self, atype_manager: ATypeManager):
        if atype_manager.atype in self._atype_to_manager:
            logging.error(f"Overwriting AType manager with AType {atype_manager.atype} in the GlobalATypesManager.")

        self._atype_to_manager[atype_manager.atype] = atype_manager

    def fetch_atype_manager(self, atype: str):
        return self._atype_to_manager[atype]

    def fetch_mod_tiers(self,
                        atype: str,
                        ilvl: int,
                        affix_types: list[ModAffixType],
                        force_mod_type=None,
                        exclude_mod_ids: set[int] = None) -> list[ModTier]:
        atype_manager = self._atype_to_manager[atype]
        mod_tiers = atype_manager.fetch_mod_tiers(ilvl=ilvl,
                                                  affix_types=affix_types,
                                                  force_mod_type=force_mod_type,
                                                  exclude_mod_ids=exclude_mod_ids)
        return mod_tiers

    def fetch_specific_mod_tiers(self,
                                 atype: str,
                                 ilvl: int,
                                 mod_ids: list[int]) -> list[ModTier]:
        atype_mod_manager = self._atype_to_manager[atype]
        mod_tiers = atype_mod_manager.fetch_specific_mods(
            ilvl=ilvl,
            mod_ids=mod_ids
        )


