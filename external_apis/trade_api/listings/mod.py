
from utils.enums import ModClass


class Mod:

    # Some mod types (ex: enchant) do not have a mod name, tier, or affix type
    def __init__(self,
                 mod_class: ModClass,
                 mod_id: str,
                 mod_text: str,
                 mod_values: tuple,
                 mod_name: str = None,
                 values_ranges: tuple = None,
                 mod_tier: int = None,
                 affix_type: str = None):
        self.mod_class = mod_class
        self.mod_id = mod_id
        self.mod_text = mod_text
        self.mod_name = mod_name
        self.mod_values = mod_values
        self.values_ranges = values_ranges
        self.mod_tier = mod_tier
        self.affix_type = affix_type
