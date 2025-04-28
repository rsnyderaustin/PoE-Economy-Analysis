
from dataclasses import dataclass

from compiled_data import Price
from things.items import Item


@dataclass
class CraftingOutcome:
    item_outcome: Item
    price: Price
    chance: float

