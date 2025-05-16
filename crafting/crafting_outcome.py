
from instances_and_definitions import ModifiableListing, ItemMod
from shared.trade_item_enums import Rarity


class CraftingOutcome:

    def __init__(self,
                 original_listing: ModifiableListing,
                 outcome_probability: float,
                 new_item_mod: ItemMod = None,
                 remove_modifier: ItemMod = None,
                 new_rarity: Rarity = None,
                 mods_fractured: list[ItemMod] = None,
                 new_quality: int = None,
                 new_sockets: int = None):

        self.original_item = original_listing
        self.probability = outcome_probability

        self.new_item_mod = new_item_mod
        self.remove_modifier = remove_modifier
        self.new_rarity = new_rarity
        self.mods_fractured = mods_fractured
        self.new_quality = new_quality
        self.new_sockets = new_sockets
