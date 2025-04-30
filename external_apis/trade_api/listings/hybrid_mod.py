
from .mod import Mod
from utils.enums import ModClass


class HybridMod:

    def __init__(self, mod_class: ModClass, mods: list[Mod]):
        self.mod_class = mod_class
        self.mods = mods
