
from .mod_tier import ModTier


class SubMod:
    def __init__(self, mod_id: str, mod_text: str, mod_tiers: list[ModTier]):
        self.mod_id = mod_id
        self.mod_text = mod_text
        self.mod_tiers = mod_tiers
