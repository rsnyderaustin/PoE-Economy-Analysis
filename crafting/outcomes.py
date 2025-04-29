
from dataclasses import dataclass

from compiled_data import Price
from things.items import Item


@dataclass
class CraftingOutcome:
    item_outcome: Item
    chance: float


class CraftingOutcomes:

    def __init__(self):
        self.outcomes_data = dict()

    def add_outcome(self, item_outcome: Item, price: Price, chance: float):
        if chance not in self.outcomes_data:
            self.outcomes_data[chance] = list()

        self.outcomes_data[chance].append(
            CraftingOutcome(
                item_outcome=item_outcome,
                price=price,
                chance=chance
            )
        )

