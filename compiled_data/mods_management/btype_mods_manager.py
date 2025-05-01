
import logging

from external_apis import ModTier
from utils.enums import ModAffixType
from .compiled_mod import CompiledMod
from .compiled_mod_with_tiers import CompiledModWithTiers


class BtypeModsManager:

    def __init__(self, btype_name: str):
        self.btype_name = btype_name

        self._coe_mod_id_to_mod = dict()
        self._coe_mod_id_to_mod_tiers_data = dict()
        self._mod_type_to_mods = dict()

    def fetch_mods(self,
                   ilvl: int,
                   force_mod_type: str = None,
                   affix_types: list[ModAffixType] = None,
                   ignore_mod_ids: set[int] = None) -> list[CompiledModWithTiers]:
        if force_mod_type:
            mods = self._mod_type_to_mods[force_mod_type]
        else:
            mods = list(self._mod_id_to_mod.values())

        if affix_types:
            mods = [mod for mod in mods if mod.affix_type in affix_types]

        if ignore_mod_ids:
            mods = [mod for mod in mods if mod not in ignore_mod_ids]

        mods_with_tiers = []
        for mod in mods:
            ilvl_to_mod_tier_dict = self._mod_id_to_mod_tiers_data[mod.coe_mod_id]
            valid_mod_tiers = [
                mod_tier
                for tier_ilvl, mod_tier in ilvl_to_mod_tier_dict.items()
                if tier_ilvl <= ilvl
            ]

            mod_with_tiers_obj = CompiledModWithTiers(
                compiled_mod=mod,
                mod_tiers=valid_mod_tiers
            )
            mods_with_tiers.append(mod_with_tiers_obj)
        return mods_with_tiers

    def add_compiled_mod(self,
                         compiled_mod: CompiledMod):
        for mod_type in compiled_mod.mod_types:
            if mod_type not in self._mod_type_to_mods:
                self._mod_type_to_mods[mod_type] = list()

            self._mod_type_to_mods[mod_type].append(compiled_mod)

        self._coe_mod_id_to_mod[compiled_mod.coe_mod_id] = compiled_mod
        self._coe_mod_id_to_mod_tiers_data[compiled_mod.coe_mod_id] = dict()

    def add_mod_tier(self,
                     mod_tier: ModTier):
        if mod_tier.coe_mod_id not in self._coe_mod_id_to_mod_tiers_data:
            logging.error(f"Could not add CoEModTier to BtypesModManager {self.btype_name}."
                          f"\nCoE Mod ID {mod_tier.coe_mod_id} not present.")

            return

        self._coe_mod_id_to_mod_tiers_data[mod_tier.coe_mod_id][mod_tier.ilvl] = mod_tier