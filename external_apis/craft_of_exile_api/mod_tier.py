

class CoEModTier:

    def __init__(self,
                 coe_mod_id: str,
                 ilvl: int,
                 values_range: tuple,
                 base_type: str):
        self.coe_mod_id = coe_mod_id
        self.ilvl = ilvl
        self.values_range = values_range
        self.base_type = base_type

