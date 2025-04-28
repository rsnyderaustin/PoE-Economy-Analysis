

class CoEMod:

    def __init__(self,
                 mod_text: str,
                 mod_id: str,
                 mod_types: list[str],
                 affix_type: str):
        self.mod_text = mod_text
        self.mod_id = mod_id
        self.mod_types = mod_types
        self.affix_type = affix_type

        self.mod_tiers = list()

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        return self.mod_id == other.mod_id

    def __hash__(self):
        return hash(self.mod_id)
