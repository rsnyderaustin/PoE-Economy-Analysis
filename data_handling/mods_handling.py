import itertools

from file_management import FilesManager, FileKey
from instances_and_definitions import ItemMod, ModClass, ModAffixType


class ItemModsManager:

    def __init__(self, mods: list[ItemMod]):
        self.mods = {}
        for mod in mods:
            if mod.affix_type not in self.mods:
                self.mods[mod.affix_type] = dict()
            self.mods[mod.affix_type][mod.mod_id] = mod

    def fetch_mod(self, affix_type: ModAffixType, mod_id):

class ModsHandler:

    def __init__(self, files_manager: FilesManager):
        self.files_manager = files_manager
        mods = files_manager.file_data[FileKey.ITEM_MODS]

    def _create_item_mods_manager(self):
        item_mods = self.files_manager.file_data[FileKey.ITEM_MODS]