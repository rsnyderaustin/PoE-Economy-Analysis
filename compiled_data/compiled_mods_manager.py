
from things import CompiledMod

class CompiledModsManager:

    def __init__(self):
        self._coe_mod_id_to_compiled_mod = dict()

    @property
    def coe_mod_ids(self) -> set:
        return set(self._coe_mod_id_to_compiled_mod.keys())

    def add_compiled_mod(self, compiled_mod: CompiledMod):
        self._coe_mod_id_to_compiled_mod[compiled_mod.coe_mod_id] = compiled_mod

    def fetch_compiled_mod(self, coe_mod_id: str):
        return self._coe_mod_id_to_compiled_mod[coe_mod_id]
