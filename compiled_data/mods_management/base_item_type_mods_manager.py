from .compiled_mod import CompiledMod
from .compiled_mod_with_tiers import CompiledModWithTiers
from things import ModTier
from utils.enums import ModAffixType


class BaseItemTypeModsManager:

    def __init__(self, base_type_id: int, base_type_name: str):
        self.base_type_id = base_type_id
        self.base_type_name = base_type_name

        self._mod_id_to_mod = dict()
        self._mod_id_to_mod_tiers_data = dict()
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

    def add_mod_tier(self,
                     base_type_id: int,
                     compiled_mod: CompiledMod,
                     ilvl: int,
                     values_range: tuple,
                     weighting: float):
        for mod_type in compiled_mod.mod_types:
            if mod_type not in self._mod_type_to_mods:
                self._mod_type_to_mods[mod_type] = set()

            self._mod_type_to_mods[mod_type].add(compiled_mod)

        if compiled_mod.coe_mod_id not in self._mod_id_to_mod:
            self._mod_id_to_mod[compiled_mod.coe_mod_id] = compiled_mod

        if compiled_mod.coe_mod_id not in self._mod_id_to_mod_tiers_data:
            self._mod_id_to_mod_tiers_data[compiled_mod.coe_mod_id] = dict()

        self._mod_id_to_mod_tiers_data[compiled_mod.coe_mod_id][ilvl] = ModTier(
            base_type_id=base_type_id,
            coe_mod_id=compiled_mod.coe_mod_id,
            ilvl=ilvl,
            values_range=values_range,
            weighting=weighting
        )
