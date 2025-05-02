
import logging

from crafting import CraftingOutcome
from crafting.crafting_engine import CraftingEngine
from things.items import Modifiable
from utils.enums import Rarity, ModAffixType
from utils import classifications
from .base_currency_engine import CurrencyEngine


class ArcanistsEtcher(CurrencyEngine):
    item_id = 'etcher'

    @classmethod
    def apply(cls, crafting_engine: CraftingEngine, item: Modifiable) -> list[CraftingOutcome]:
        if item.corrupted:
            return [cls.no_outcome_change(item=item)]

        if item.category not in classifications.non_martial_weapons:
            return [cls.no_outcome_change(item=item)]

        item_quality = item.quality if item.quality else 0

        if item.rarity == Rarity.NORMAL:
            quality_increase = 5
        elif item.rarity == Rarity.MAGIC:
            quality_increase = 2
        elif item.rarity in (Rarity.RARE, Rarity.UNIQUE):
            quality_increase = 1
        else:
            logging.info(f"{cls.__name__} not applicable to item with rarity {item.rarity}.")
            return [cls.no_outcome_change(item=item)]

        if item_quality == item.maximum_quality:
            return [cls.no_outcome_change(item=item)]

        return [
            CraftingOutcome(
                original_item=item,
                outcome_probability=1.0,
                new_quality=min(item.maximum_quality, item_quality + quality_increase)
            )
        ]


