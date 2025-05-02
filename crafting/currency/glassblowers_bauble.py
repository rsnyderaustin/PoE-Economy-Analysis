
from crafting import CraftingOutcome
from crafting.crafting_engine import CraftingEngine
from things.items import Modifiable
from utils.enums import ItemCategory
from .base_currency_engine import CurrencyEngine


class ArtificersOrb(CurrencyEngine):

    item_id='artificers'

    @classmethod
    def apply(cls, crafting_engine: CraftingEngine, item: Modifiable) -> list[CraftingOutcome]:
        if item.corrupted:
            return [cls.no_outcome_change(item=item)]

        if item.category != ItemCategory.ANY_FLASK:
            return [cls.no_outcome_change(item=item)]

        item_quality = item.quality if item.quality else 0

        return [
            CraftingOutcome(
                original_item=item,
                outcome_probability=1.0,
                new_quality=min(item.maximum_quality, item_quality + 1)
            )
        ]
