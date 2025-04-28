
from items.attributes import Mod

class ModTierInfo:

    def __init__(self,
                 mod: Mod,
                 ilvl_requirement: int,
                 values_range: tuple,
                 weighting: int):
        self.mod = mod
        self.ilvl_requirement = ilvl_requirement
        self.values_range = values_range
        self.weighting = weighting
    official_poe_mod_id: str
    craft_of_exile_mod_id: str
    ilvl_requirement: int
    values_range: tuple
    weighting: int
