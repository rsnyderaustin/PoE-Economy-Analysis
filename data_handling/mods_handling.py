import itertools

from file_management import FilesManager, FileKey
from instances_and_definitions import ItemMod, ModClass, ModAffixType


class ItemModsManager:

    def __init__(self, mods: list[ItemMod] = None):
        self.mods = {}

        if mods:
            self.add_mods(mods)

    def add_mods(self, mods: list[ItemMod]):
        for mod in mods:
            if mod.atype not in self.mods:
                self.mods[mod.atype] = dict()

            if mod.mod_id not in self.mods[mod.mod_id]:
                self.mods[mod.atype][mod.mod_id] = dict()

            self.mods[mod.atype][mod.mod_id] = mod

    def fetch_mod(self, atype: str, mod_id: str):
        return self.mods[atype][mod_id]


class ModsHandler:

    def __init__(self, files_manager: FilesManager):
        self.files_manager = files_manager
        mods = files_manager.file_data[FileKey.ITEM_MODS]

    def _create_item_mods_manager(self):
        item_mods = self.files_manager.file_data[FileKey.ITEM_MODS]