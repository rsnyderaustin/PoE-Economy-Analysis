
from dataclasses import dataclass

from api_mediation import Price
from items import Item


@dataclass
class CraftingOutcome:
    item_outcome: Item
    price: Price
    chance: float

