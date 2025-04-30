
from dataclasses import dataclass
import logging

from utils.enums import ModAffixType


class CompiledMod:

    def __init__(self, official_mod_ids: list[str], coe_mod_id: str, coe_mod_text: str, mod_types: list[str], affix_type: str):
        # A mod can have multiple Official Mod IDs if that mod is a hybrid mod
        self.official_mod_ids = official_mod_ids
        self.coe_mod_id = coe_mod_id
        self.coe_mod_text = coe_mod_text

        # A mod can have multiple mod types (ex: [Mana, Lightning]
        self.mod_types = mod_types
        self.affix_type = affix_type

    def __eq__(self, other):
        if not isinstance(other, CompiledMod):
            return False

        return self.coe_mod_id == other.coe_mod_id

    def __hash__(self):
        return hash(self.coe_mod_id)

