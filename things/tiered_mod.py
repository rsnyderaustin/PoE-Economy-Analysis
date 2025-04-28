
from dataclasses import dataclass
import logging

from utils.enums import ModAffixType


@dataclass
class ModTier:
    official_mod_id: str
    coe_mod_id: str
    affix_type: ModAffixType
    ilvl: int
    values_range: tuple
    weighting: float


class TieredMod:

    def __init__(self, official_mod_ids: list[str], coe_mod_id: str, readable_name: str, mod_types: list[str], affix_type: str):
        # A mod can have multiple Official Mod IDs if that mod is a hybrid mod
        self.official_mod_ids = official_mod_ids
        self.coe_mod_id = coe_mod_id
        self.readable_name = readable_name

        # A mod can have multiple mod types (ex: [Mana, Lightning]
        self.mod_types = mod_types
        self.affix_type = affix_type

        self.data = dict()

    def add_tier(self, ilvl: int, values_range: tuple, weighting: float):
        if ilvl in self.data:
            logging.error(f"Asked to replace mod with Craft of Exile ID {self.coe_mod_id} for ilvl {ilvl} and mod_type {self.mod_type}.")
        self.data[ilvl] = ModTier(ilvl=ilvl,
                                  values_range=values_range,
                                  weighting=weighting,
                                  affix_type=self.affix_type)

    def fetch_modifiers(self, max_ilvl: int) -> list[ModTier]:
        valid_mods = [
            mod_tier for ilvl, mod_tier in self.data.items()
            if ilvl <= max_ilvl
        ]
        return valid_mods

