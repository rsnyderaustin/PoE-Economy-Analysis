
import logging

from .compiled_mod import CompiledMod


class CompiledModsManager:

    def __init__(self):
        self._coe_mod_id_to_compiled_mod = dict()
        self._coe_mod_text_to_compiled_mod = dict()

    @property
    def coe_mod_ids(self) -> set[int]:
        return set(self._coe_mod_id_to_compiled_mod.keys())

    def add_compiled_mod(self, compiled_mod: CompiledMod):
        self._coe_mod_id_to_compiled_mod[compiled_mod.coe_mod_id] = compiled_mod
        self._coe_mod_text_to_compiled_mod[compiled_mod.coe_mod_text] = compiled_mod

    def fetch_compiled_mod(self, coe_mod_id: id = None, coe_mod_text: str = None) -> CompiledMod | None:
        if coe_mod_id:
            if coe_mod_id not in self._coe_mod_id_to_compiled_mod:
                logging.error(f"Requested to fetch non-existent mod {coe_mod_id}. It probably just didn't have a match.")
                return None
            return self._coe_mod_id_to_compiled_mod[coe_mod_id]

        if coe_mod_text:
            if coe_mod_text not in self._coe_mod_text_to_compiled_mod:
                logging.error(
                    f"Requested to fetch non-existent mod {coe_mod_text}. It probably just didn't have a match.")
                return None
            return self._coe_mod_text_to_compiled_mod[coe_mod_text]

