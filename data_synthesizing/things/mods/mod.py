from utils.enums import ModAffixType
from .mod_tier import ModTier
from .sub_mod import SubMod


def _determine_mod_id(atype: str, mod_ids: list[str]):
    if len(mod_ids) == 1:
        return mod_ids[0]
    else:
        return f"{atype}_{'_'.join(mod_ids)}"


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


class Mod:

    # Some mod types (ex: enchant) do not have a mod name, tier, or affix type
    # Rune mods do not always have a mod ID, so for consistencies sake none of the runes will have IDs
    def __init__(self,
                 sub_mods: list[SubMod],
                 mod_name: str = None,
                 mod_types: list[str] = None,
                 atype: str = None,
                 mod_tier: int = None,
                 affix_type: ModAffixType = None):
        """

        :param sub_mods: Should be in text order per the full mod text.
        :param mod_name:
        :param atype: Attribute type (ie: DEX Body Armour)
        """
        self.sub_mods = sub_mods
        self.mod_id = _determine_mod_id(atype=atype,
                                        mod_ids=[sub_mod.mod_id for sub_mod in sub_mods])
        self.mod_name = mod_name
        self.mod_types = mod_types
        self.atype = atype
        self.affix_type = affix_type
        self.mod_tier = mod_tier

        self._mod_tiers_manager = ModTiersManager()

    def __eq__(self, other):
        if not isinstance(other, Mod):
            return False

        return self.mod_id == other.mod_id

    def __hash__(self):
        return hash(self.mod_id)

    @property
    def is_hybrid(self):
        return len(self.sub_mods) >= 2

    def add_mod_tier(self,
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
        self._mod_tiers_manager.add_mod_tier(new_mod_tier)

    def fetch_mod_tiers(self, max_ilvl: int) -> list[ModTier]:
        return self._mod_tiers_manager.fetch_mod_tiers(max_ilvl)
