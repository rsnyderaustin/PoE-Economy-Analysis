
import logging

from data_synthesizing.things.mods.singleton_mod import Mod
from shared.enums import ModAffixType


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
