from data_synthesizing import GlobalATypesManager, ModTier
from things.items import Modifiable
from utils.enums import ModAffixType
from .crafting_outcome import CraftingOutcome


class CraftingEngine:

    def __init__(self, global_atypes_manager: GlobalATypesManager):
        self.global_atypes_manager = global_atypes_manager

    def fetch_atype_mod_tiers(self,
                              item: Modifiable,
                              mod_ids: list[int]) -> list[ModTier]:
        return self.global_atypes_manager.fetch_specific_mod_tiers(
            atype=item.atype,
            ilvl=item.ilvl,
            mod_ids=mod_ids
        )

    def roll_new_modifier(self,
                          item: Modifiable,
                          affix_types: list[ModAffixType],
                          force_type: str = None,
                          exclude_mod_ids: set = None) -> list[ModTier]:
        """

        :param item:
        :param affix_types:
        :param force_type:
        :param exclude_mod_ids: If not supplied, the function assumes that all current mods on the item are not eligible to roll.
        :return:
        """

        atype_mod_tiers = self.global_atypes_manager.fetch_mod_tiers(
            atype=item.atype,
            ilvl=item.ivl,
            force_mod_type=force_type,
            exclude_mod_ids=set(mod.mod_id for mod in item.explicit_mods) if not exclude_mod_ids else exclude_mod_ids,
            affix_types=affix_types
        )

        return atype_mod_tiers


    def create_crafting_outcomes(self,
                                 item: Modifiable,
                                 mod_tiers: list[ModTier],
                                 exclude_mod_ids: list[int] = None) -> list[CraftingOutcome]:
        mod_tiers = [mod_tier for mod_tier in mod_tiers
                     if mod_tier.parent_mod_id not in exclude_mod_ids]
        total_mod_weight = sum(
            mod_tier.weighting
            for mod_tier in mod_tiers
        )

        crafting_outcomes = []
        for mod_tier in mod_tiers:
            crafting_outcome = CraftingOutcome(
                original_item=item,
                outcome_probability=mod_tier.weighting / total_mod_weight,
                new_mod_tier=mod_tier
            )
            crafting_outcomes.append(crafting_outcome)

        return crafting_outcomes
