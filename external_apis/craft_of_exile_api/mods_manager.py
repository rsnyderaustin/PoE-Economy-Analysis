
from .mod import CoEMod


class CoEModsManager:

    def __init__(self):
        self.mod_id_to_mod_text = dict()
        self.mod_text_to_mod_id = dict()

    @property
    def mod_ids(self) -> set:
        return set(self.mod_id_to_mod_text.keys())

    @property
    def mod_texts(self) -> set:
        return set(self.mod_text_to_mod_id.keys())

    def add_mod(self, mod: CoEMod):
        self.mod_id_to_mod_text[mod.coe_mod_id] = mod
        self.mod_text_to_mod_id[mod.coe_mod_text] = mod

    def fetch_mod(self, mod_id: str = None, mod_text: str = None) -> CoEMod:
        if mod_id:
            return self.mod_id_to_mod_text[mod_id]
        elif mod_text:
            return self.mod_text_to_mod_id[mod_text]