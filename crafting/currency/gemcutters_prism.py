from crafting import CraftingOutcome
from crafting.crafting_engine import CraftingEngine
from things.items import Modifiable
from utils.enums import Rarity, ModAffixType, ItemCategory
from .base_currency_engine import CurrencyEngine


class GemcuttersPrism(CurrencyEngine):
    item_id = 'gcp'

    @classmethod
    def apply(cls, crafting_engine: CraftingEngine, item: Modifiable) -> list[CraftingOutcome]:
        if item.btype != ItemCategory.ANY_GEM:
            return [cls.no_outcome_change(item=item)]

        if item.corrupted:
            return [cls.no_outcome_change(item=item)]

        return [
            CraftingOutcome(
                original_item=item,
                outcome_probability=1.0,
                quality_change=5
            )
        ]
