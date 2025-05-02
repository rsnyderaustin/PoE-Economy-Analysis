from crafting import CraftingOutcome
from crafting.crafting_engine import CraftingEngine
from things.items import Modifiable
from utils.enums import Rarity, ModAffixType
from .base_currency_engine import CurrencyEngine


class OrbOfAnnulment(CurrencyEngine):
    item_id = 'annul'

    @classmethod
    def apply(cls, crafting_engine: CraftingEngine, item: Modifiable) -> list[CraftingOutcome]:
        if not item.explicit_mods:
            return [cls.no_outcome_change(item=item)]

        if item.corrupted:
            return [cls.no_outcome_change(item=item)]

        outcomes = []
        for mod in item.removable_mods:
            outcomes.append(
                CraftingOutcome(
                    original_item=item,
                    outcome_probability=(1 / len(item.removable_mods)),
                    remove_modifier=mod
                )
            )

        return outcomes