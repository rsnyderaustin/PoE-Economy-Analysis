
class ModTier:

    def __init__(self,
                 parent_mod_id: str,
                 affix_type: str,
                 atype: str,
                 mod_id_to_values_ranges: dict[str: list],
                 ilvl: int,
                 weighting: float):
        self.parent_mod_id = parent_mod_id
        self.affix_type = affix_type
        self.atype = atype
        self.mod_id_to_values_ranges = mod_id_to_values_ranges
        self.ilvl = ilvl
        self.weighting = weighting
