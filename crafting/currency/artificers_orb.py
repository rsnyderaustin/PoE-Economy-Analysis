
from crafting import CraftingOutcome
from crafting.crafting_engine import CraftingEngine
from things.items import Modifiable
from .base_currency_engine import CurrencyEngine


class ArtificersOrb(CurrencyEngine):

    item_id='artificers'

    @classmethod
    def apply(cls, crafting_engine: CraftingEngine, item: Modifiable) -> list[CraftingOutcome]:
        max_atype_sockets = helper_funcs.determine_max_sockets(atype=atype)

        if item.corrupted:
            return [cls.no_outcome_change(item=item)]

        if max_atype_sockets == 0:
            return [cls.no_outcome_change(item=item)]

        item_sockets = 0 if not item.num_sockets else item.num_sockets

        if item_sockets < max_atype_sockets:
            return [
                CraftingOutcome(
                    original_item=item,
                    outcome_probability=1.0,
                    new_sockets=1
                )
            ]
