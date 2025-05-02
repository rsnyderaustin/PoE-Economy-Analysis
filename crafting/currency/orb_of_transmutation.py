
from crafting import CraftingOutcome
from crafting.crafting_engine import CraftingEngine
from things.items import Modifiable
from utils.enums import Rarity, ModAffixType
from .base_currency_engine import CurrencyEngine


class OrbOfTransmutation(CurrencyEngine):
    item_id = 'transmute'

    @classmethod
    def apply(cls, crafting_engine: CraftingEngine, item: Modifiable) -> list[CraftingOutcome]:
        if item.corrupted:
            return [cls.no_outcome_change(item=item)]

        if item.rarity != Rarity.NORMAL:
            return [cls.no_outcome_change(item=item)]

        outcomes = crafting_engine.roll_new_modifier(item=item,
                                                     affix_types=[ModAffixType.SUFFIX, ModAffixType.PREFIX])
        for outcome in outcomes:
            outcome.new_rarity = Rarity.MAGIC

        return outcomes


