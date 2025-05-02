
from crafting import CraftingOutcome
from crafting.crafting_engine import CraftingEngine
from things.items import Modifiable
from utils.enums import Rarity, ModAffixType
from .base_currency_engine import CurrencyEngine


class ExaltedOrb(CurrencyEngine):
    item_id = 'exalt'

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

        if not open_prefixes and not open_suffixes:
            return [
                cls.no_outcome_change(item=item)
            ]

        affix_types = []
        if open_prefixes:
            affix_types.append(ModAffixType.PREFIX)

        if open_suffixes:
            affix_types.append(ModAffixType.SUFFIX)

        possible_mod_tiers = crafting_engine.roll_new_modifier(item=item,
                                                               affix_types=affix_types)
        crafting_outcomes = crafting_engine.create_crafting_outcomes(item=item,
                                                                     mod_tiers=possible_mod_tiers)
        return crafting_outcomes
