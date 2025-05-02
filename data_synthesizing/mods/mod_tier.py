

class ModTier:

    def __init__(self,
                 atype: str,
                 mod_id_to_values_ranges: dict[str: list],
                 parent_mod_id: str,
                 ilvl: int,
                 weighting: float):
        self.atype = atype
        self.mod_id_to_values_ranges = mod_id_to_values_ranges
        self.parent_mod_id = parent_mod_id
        self.ilvl = ilvl
        self.weighting = weighting
