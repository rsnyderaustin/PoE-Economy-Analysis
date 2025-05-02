
from crafting import CraftingOutcome
from crafting.crafting_engine import CraftingEngine
from things.items import Modifiable
from utils.enums import Rarity, ModAffixType
from .base_currency_engine import CurrencyEngine


class RegalOrb(CurrencyEngine):
    item_id = 'regal'

    @classmethod
    def apply(cls, crafting_engine: CraftingEngine, item: Modifiable) -> list[CraftingOutcome]:
        if item.rarity != Rarity.MAGIC:
            return [cls.no_outcome_change(item=item)]

        if item.corrupted:
            return [cls.no_outcome_change(item=item)]

        possible_mod_tiers = crafting_engine.roll_new_modifier(item=item,
                                                               affix_types=[ModAffixType.SUFFIX, ModAffixType.PREFIX])
        crafting_outcomes = crafting_engine.create_crafting_outcomes(item=item,
                                                                     mod_tiers=possible_mod_tiers)
        for outcome in crafting_outcomes:
            outcome.new_rarity = Rarity.RARE

        return crafting_outcomes
