from shared.enums import ModAffixType


class SubMod:
    def __init__(self, mod_id: str, affix_type: ModAffixType, mod_text: str):
        self.mod_id = mod_id
        self.affix_type = affix_type
        self.mod_text = mod_text
