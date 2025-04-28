from crafting import CraftingOutcome
from items import Gem, Item, Modifiable
from utils import Currency, ItemAttributes, Rarity, ModifierType


class CraftingSimulator:

    def _corrupt_item(self, item: Item, omen_used: bool):
        if isinstance(item, Gem):
            return

        if not hasattr(item, ItemAttributes.MiscAttribute.RARITY.value):
            raise AttributeError(f"Attempted to corrupt non-gem {item.name} of class {type(item)}.")

        if item.rarity == Rarity.UNIQUE:

    def roll_new_modifier(self, item: Modifiable, modifier_types: list[ModifierType]) -> list[CraftingOutcome]:
        open_prefixes = itenm


