
import logging

from shared.enums import ModAffixType

from data_synthesizing.things.mods.singleton_mod import Mod


class ATypeManager:

    def __init__(self, atype: str):
        self.atype = atype
        self._mod_id_to_mod = dict()

    @property
    def mods(self) -> set[Mod]:
        return set(self._mod_id_to_mod.values())

    def add_mod(self, mod: Mod):
        if not mod.atype != self.atype:
            raise TypeError(f"Attempted to add mod with AType {mod.atype} to ATypeManager with AType {self.atype}.")

        if mod.mod_id in self._mod_id_to_mod:
            logging.error(f"Overwriting Mod with Mod ID {mod.mod_id} in AType manager with AType {self.atype}")

        self._mod_id_to_mod[mod.mod_id] = mod

    def fetch_mod(self, mod_id: str):
        return self._mod_id_to_mod[mod_id]

    def fetch_mod_tiers(self,
                        ilvl: int,
                        force_mod_type: str = None,
                        exclude_mod_ids: set[str] = None,
                        affix_types: list[ModAffixType] = None):
        mod_tiers = list()
        for mod in self.mods:
            if force_mod_type and force_mod_type not in mod.mod_types:
                continue

            if affix_types and mod.affix_type_enum not in affix_types:
                continue

            if exclude_mod_ids and mod.mod_id in exclude_mod_ids:
                continue

            viable_mod_tiers = mod.fetch_mod_tiers(max_ilvl=ilvl)
            mod_tiers.append(viable_mod_tiers)

        return mod_tiers


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
