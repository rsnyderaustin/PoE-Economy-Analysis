

class CoEMod:

    def __init__(self,
                 coe_mod_text: str,
                 coe_mod_id: str,
                 mod_types: list[str],
                 affix_type: str):
        self.coe_mod_text = coe_mod_text
        self.coe_mod_id = coe_mod_id
        self.mod_types = mod_types
        self.affix_type = affix_type

        self.mod_tiers = list()

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        return self.coe_mod_id == other.coe_mod_id

    def __hash__(self):
        return hash(self.coe_mod_id)
