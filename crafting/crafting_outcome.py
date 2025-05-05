
from utils.enums import Rarity

from data_synthesizing import ModTier
from things.items import Modifiable


class CraftingOutcome:

    def __init__(self,
                 original_item: Modifiable,
                 outcome_probability: float,
                 new_mod_tier: ModTier = None,
                 remove_modifier: ModTier = None,
                 new_rarity: Rarity = None,
                 mods_fractured: list[ModTier] = None,
                 new_quality: int = None,
                 new_sockets: int = None):

        self.original_item = original_item
        self.outcome_probability = outcome_probability

        self.new_mod_tier = new_mod_tier
        self.remove_modifier = remove_modifier
        self.new_rarity = new_rarity
        self.mods_fractured = mods_fractured
        self.new_quality = new_quality
        self.new_sockets = new_sockets
