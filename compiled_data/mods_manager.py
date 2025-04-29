
from things import CompiledMod


class CompiledModsManager:

    def __init__(self):
        self.official_id_to_mod = dict()
        self.coe_id_to_mod = dict()

    def add_mod(self, tiered_mod: CompiledMod):
        self.official_id_to_mod[tiered_mod.official_mod_id] = tiered_mod
        self.coe_id_to_mod[tiered_mod.coe_mod_id] = tiered_mod

