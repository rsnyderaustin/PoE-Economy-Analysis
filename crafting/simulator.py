
import logging

from api_mediation import Price, ModTierInfo
from crafting import CraftingOutcome
from items import Gem, Item, Modifiable
from utils import Currency, ItemAttributes, Rarity, ModifierType
from utils.enums import ModAffixType


class CraftingSimulator:

    def _corrupt_item(self, item: Item, omen_used: bool):
        if isinstance(item, Gem):
            return

        if not hasattr(item, ItemAttributes.MiscAttribute.RARITY.value):
            raise AttributeError(f"Attempted to corrupt non-gem {item.name} of class {type(item)}.")

        if item.rarity == Rarity.UNIQUE:

    def _fetch_mod_tiers(self,
                         item: Modifiable,
                         affix_type: ModAffixType,
                         mod_type: ModifierType = None) -> list[ModTierInfo]:
        pass

    def roll_new_modifier(self,
                          item: Modifiable,
                          current_price: Price,
                          mod_type: ModifierType) -> list[CraftingOutcome]:
        open_prefixes = 3 - len(item.prefixes)
        open_suffixes = 3 - len(item.suffixes)
        open_affixes = open_prefixes + open_suffixes

        if not open_affixes:
            logging.info(f"Attempted to roll a new modifier on item {item.__dict__} when item has no open affixes.")
            return [CraftingOutcome(item_outcome=item, price=current_price, chance=1.0)]

        outcomes = list()
        if open_prefixes:
            odds_to_roll_prefix = open_prefixes / open_affixes

            mods = self._fetch_mod_tiers(item=item,
                                         affix_type=ModAffixType.PREFIX,
                                         mod_type=mod_type)
            total_mods_weight = sum([mod.weighting for mod in mods])
            prefix_outcomes = [
                CraftingOutcome(
                    item_outcome=item.explicit_mods
                )
            ]

        if open_suffixes:
            odds_to_roll_suffix = open_suffixes / open_affixes



