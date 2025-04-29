
from .base_currency_engine import CurrencyEngine
from crafting.crafting_engine import CraftingEngine
from crafting import CraftingOutcome
from things.items import Modifiable
from utils.enums import Rarity

class ExaltedOrb(CurrencyEngine):

    item_id = 'exalt'
    readable_name = 'exalted-orb'

    @classmethod
    def apply(cls, item: Modifiable, current_price: float) -> CraftingOutcome:
        if item.rarity != Rarity.RARE:
            return CraftingOutcome(
                item_outcome=item,
                chance=1.00
            )
        
        outcomes = CraftingEngine.roll_new_modifier(item=item)
        return outcomes
