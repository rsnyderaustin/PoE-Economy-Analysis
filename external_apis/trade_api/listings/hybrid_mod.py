
from .mod import Mod
from utils.enums import ModClass, ModAffixType


class HybridMod:

    def __init__(self,
                 mod_class: ModClass,
                 mods: list[Mod],
                 affix_type: ModAffixType,
                 mod_name: str,
                 mod_tier: int,
                 ):
        self.mod_class = mod_class
        self.mods = mods
        self.affix_type = affix_type
