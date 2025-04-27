from items import Gem, Item
from utils import Currency, ItemAttributes, Rarity


class CraftingSimulator:

    def _corrupt_item(self, item: Item, omen_used: bool):
        if isinstance(item, Gem):
            return

        if not hasattr(item, ItemAttributes.MiscAttribute.RARITY.value):
            raise AttributeError(f"Attempted to corrupt non-gem {item.name} of class {type(item)}.")

        if item.rarity == Rarity.UNIQUE:





    @classmethod
    def simulate(cls, item: Item, currency: Currency):


