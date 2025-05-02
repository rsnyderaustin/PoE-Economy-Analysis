
from abc import ABC, abstractmethod

from crafting import CraftingOutcome
from crafting.crafting_engine import CraftingEngine
from things.items import Modifiable


class CurrencyEngine(ABC):

    @abstractmethod
    def apply(self, crafting_engine: CraftingEngine, item: Modifiable):
        pass

    @staticmethod
    def no_outcome_change(item: Modifiable) -> CraftingOutcome:
        return CraftingOutcome(
            original_item=item,
            outcome_probability=1.0
        )
