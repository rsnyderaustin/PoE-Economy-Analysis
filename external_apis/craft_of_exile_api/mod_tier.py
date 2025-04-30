

class CoEModTier:

    def __init__(self,
                 coe_mod_id: str,
                 ilvl: int,
                 values_range: tuple,
                 btype_name: str,
                 weighting: float):
        self.coe_mod_id = coe_mod_id
        self.ilvl = ilvl
        self.values_range = values_range
        self.btype_name = btype_name
        self.weighting = weighting

