from file_management import FilesManager, FileKey
from instances_and_definitions import ModClass


class ModMatcher:

    pass


class ModSynthesizer:

    def __init__(self, files_manager: FilesManager):
        self.files_manager = files_manager
        self.item_mods_manager = files_manager.file_data[FileKey.]

    def synthesize_mod(self, mod_class: ModClass, atype: str, mod_ids: list[str]):

