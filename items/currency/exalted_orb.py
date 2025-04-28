
from .base_currency import Currency
from crafting import CraftingOutcome
from items import Item, Modifiable
from utils.enums import ModifierType

class ExaltedOrb(Currency):

    def __init__(self):
        super(Currency).__init__(item_id='exalted',
                                 readable_name='Exalted Orb')

    def modify_item(self, item: Item) -> list[CraftingOutcome]:
        if not isinstance(item, Modifiable):
            raise TypeError(f"Item with type {type(item)} is not correct type Modifiable.")
        item.roll_


