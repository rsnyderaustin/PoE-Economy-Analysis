
from .mod import OfficialMod


class OfficialModsManager:

    def __init__(self):
        self.mods_by_mod_id = dict()
        self.mods_by_mod_text = dict()

    def add_mod(self, mod: OfficialMod):
        self.mods_by_mod_id[mod.mod_id] = mod
        self.mods_by_mod_text[mod.mod_text] = mod

    def fetch_mod(self, mod_id: str = None, mod_text: str = None):
        if mod_id:
            return self.mods_by_mod_id[mod_id]
        elif mod_text:
            return self.mods_by_mod_text[mod_text]

