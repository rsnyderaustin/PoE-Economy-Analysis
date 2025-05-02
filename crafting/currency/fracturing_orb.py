

from crafting import CraftingOutcome
from crafting.crafting_engine import CraftingEngine
from things.items import Modifiable
from utils.enums import Rarity, ModAffixType
from .base_currency_engine import CurrencyEngine


class FracturingOrb(CurrencyEngine):

    item_id = 'fracturing-orb'

    @classmethod
    def apply(cls, crafting_engine: CraftingEngine, item: Modifiable) -> list[CraftingOutcome]:
        if item.corrupted:
            return [cls.no_outcome_change(item=item)]

        if item.fractured_mods:
            return [cls.no_outcome_change(item=item)]

        outcomes = []
        for mod in item.explicit_mods:
            outcomes.append(
                CraftingOutcome(
                    original_item=item,
                    outcome_probability=(1.0 / len(item.explicit_mods)),
                    mods_fractured=mod
                )
            )

        return outcomes

