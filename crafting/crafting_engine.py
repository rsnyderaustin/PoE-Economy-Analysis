
from .base_type_mods_manager import BaseTypeModsManager
from .outcomes import CraftingOutcome
from things import Currency
from things.items import Modifiable

class CraftingEngine:

    def __init__(self, base_type_mods_manager: BaseTypeModsManager):
        self.mods_manager = base_type_mods_manager

    @classmethod
    def roll_new_modifier(cls, item: Modifiable, force_type: str = None) -> list[CraftingOutcome]:

