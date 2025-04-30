from utils.enums import ModAffixType
from external_apis.craft_of_exile_api.global_btypes_manager import GlobalBtypesManager
from .outcomes import CraftingOutcome
from things.items import Modifiable


class CraftingEngine:

    def __init__(self, global_mods_manager: GlobalBtypesManager):
        self.global_mods_manager = global_mods_manager

    def roll_new_modifier(self,
                          item: Modifiable,
                          force_type: str = None) -> list[CraftingOutcome]:
        has_open_suffix = 3 > len(item.suffixes)
        has_open_prefix = 3 > len(item.prefixes)

        if item.corrupted:
            return [
                CraftingOutcome(
                    item_outcome=item,
                    chance=1.00
                )
            ]

        if not has_open_suffix and not has_open_prefix:
            return [
                CraftingOutcome(
                    item_outcome=item,
                    chance=1.00
                )
            ]

        open_affix_types = list()
        if has_open_suffix:
            open_affix_types.append(ModAffixType.SUFFIX)

        if has_open_prefix:
            open_affix_types.append(ModAffixType.PREFIX)

        mods_with_tiers = self.global_mods_manager.fetch_mods_and_tiers(
            btype_name=item.btype,
            ilvl=item.ilvl,
            force_mod_type=force_type,
            ignore_mod_ids=set(mod.coe_mod_id for mod in item.explicit_mods),
            affix_types=open_affix_types
        )

        weighting_sum = sum(
            [
                mod_tier.weighting
                for mod_with_tier in mods_with_tiers
                for mod_tier in mod_with_tier.mod_tiers
            ]
        )


