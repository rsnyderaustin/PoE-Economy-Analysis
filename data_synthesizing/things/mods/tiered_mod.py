from shared.enums import ModAffixType
from .singleton_mod import Mod
from .mod_tier import ModTier
from .. import SubMod
from .base_mod_class import generate_mod_id


class ModTiersManager:

    def __init__(self):
        self._ilvl_to_mod_tier = dict()

    def add_mod_tier(self, mod_tier: ModTier):
        if mod_tier.ilvl not in self._ilvl_to_mod_tier:
            self._ilvl_to_mod_tier[mod_tier.ilvl] = mod_tier

    def fetch_mod_tiers(self, max_ilvl: int) -> list[ModTier]:
        valid_ilvls = [
            ilvl for ilvl in self._ilvl_to_mod_tier.keys()
            if ilvl <= max_ilvl
        ]
        return [self._ilvl_to_mod_tier[ilvl] for ilvl in valid_ilvls]


class TieredMod(Mod):

    def __init__(self,
                 atype: str,
                 sub_mods: list[SubMod],
                 mod_text: str,
                 mod_tiers: list[ModTier],
                 mod_name: str,
                 mod_types: list[str],
                 affix_type: ModAffixType = None
                 ):

        mod_id = generate_mod_id(atype=atype,
                                 mod_ids=[sub_mod.mod_id for sub_mod in sub_mods],
                                 mod_text=mod_text)
        super().__init__(mod_id=mod_id)
        self.atype = atype
        self.sub_mods = sub_mods

        self._mod_tiers_manager = ModTiersManager()
        for mod_tier in mod_tiers:
            self._mod_tiers_manager.add_mod_tier(mod_tier)

        self.mod_name = mod_name
        self.mod_types = mod_types
        self.affix_type = affix_type

    @property
    def is_hybrid(self):
        return len(self.sub_mods) >= 2

    def add_mod_tier(self,
                     mod_tier: ModTier,
                     ilvl: int,
                     mod_id_to_values_ranges: dict[str: list],
                     weighting: float
                     ):
        new_mod_tier = ModTier(
            parent_mod_id=self.mod_id,
            atype=self.atype,
            mod_id_to_values_ranges=mod_id_to_values_ranges,
            ilvl=ilvl,
            weighting=weighting
        )
        self._mod_tiers_manager.add_mod_tier(mod_tier)

    def fetch_mod_tiers(self, max_ilvl: int) -> list[ModTier]:
        return self._mod_tiers_manager.fetch_mod_tiers(max_ilvl)

