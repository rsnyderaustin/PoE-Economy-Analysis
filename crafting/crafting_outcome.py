
from things.items import Modifiable
from utils.enums import Rarity


class CraftingOutcome:

    def __init__(self,
                 original_item: Modifiable,
                 outcome_probability: float,
                 new_modifier: ModTier = None,
                 remove_modifier: ModTier = None,
                 new_rarity: Rarity = None):

        self.original_item = original_item
        self.outcome_probability = outcome_probability

        self.new_modifier = new_modifier
        self.remove_modifier = remove_modifier
        self.new_rarity = new_rarity
