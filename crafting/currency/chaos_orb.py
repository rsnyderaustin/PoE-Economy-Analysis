import copy

from crafting import CraftingOutcome
from crafting.crafting_engine import CraftingEngine
from things.items import Modifiable
from utils.enums import Rarity, ModAffixType
from .base_currency_engine import CurrencyEngine


class ChaosOrb(CurrencyEngine):
    item_id = 'chaos'

    @classmethod
    def apply(cls, crafting_engine: CraftingEngine, item: Modifiable) -> list[CraftingOutcome]:
        if item.rarity != Rarity.RARE:
            return [
                cls.no_outcome_change(item=item)
            ]

        if item.corrupted:
            return [
                cls.no_outcome_change(item=item)
            ]

        open_prefixes = 3 - len(item.prefixes)

        open_suffixes = 3 - len(item.suffixes)

        irremovable_mod_ids = set(
            unremovable_mod.mod_id for unremovable_mod in item.permanent_mods
        )

        returnable_outcomes = []
        # If there are open prefixes, then we can roll any prefix no matter what is removed. The same is true for suffixes.
        # Note that when rolling for a new modifier, chaos orbs can replace the same mod they just removed with the same mod.
        # So we pass only the modifiers that cannot be removed (fractured mods) to exclude_mod_ids parameter
        possible_mod_tiers = crafting_engine.roll_new_modifier(item=item,
                                                               affix_types=[ModAffixType.SUFFIX, ModAffixType.PREFIX],
                                                               exclude_mod_ids=irremovable_mod_ids)
        for modifier in item.explicit_mods:
            if open_prefixes and open_suffixes:
                viable_mod_tiers = possible_mod_tiers
            # If we rolled a prefix and there are no open suffixes then we CANNOT roll a suffix
            elif modifier.affix_type == ModAffixType.PREFIX and not open_suffixes:
                viable_mod_tiers = [mod for mod in possible_mod_tiers if mod.affix_type == ModAffixType.PREFIX]
            # If we rolled a suffix and there are no open prefixes then we CANNOT roll a prefix
            elif modifier.affix_type == ModAffixType.SUFFIX and not open_prefixes:
                viable_mod_tiers = [mod for mod in possible_mod_tiers if mod.affix_type == ModAffixType.SUFFIX]
            # In all other cases, we can roll any mod
            else:
                viable_mod_tiers = possible_mod_tiers

            other_mod_ids = [item_mod.mod_id for item_mod in item.mods if item_mod != modifier]
            crafting_outcomes = crafting_engine.create_crafting_outcomes(
                item=item,
                mod_tiers=viable_mod_tiers,
                exclude_mod_ids=other_mod_ids,
            )
            
            for outcome in crafting_outcomes:
                outcome.remove_modifier = modifier
                outcome.outcome_probability /= len(item.explicit_mods)

            returnable_outcomes.extend(crafting_outcomes)

        return returnable_outcomes
