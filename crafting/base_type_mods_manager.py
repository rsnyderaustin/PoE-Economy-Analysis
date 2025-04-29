
from compiled_data import CompiledModsManager

class BaseTypeModsManager:

    def __init__(self, compiled_mods_managers: list[CompiledModsManager]):
        self.base_type_id_to_mods_manager = {
            mods_manager.base_type_id: mods_manager
            for mods_manager in compiled_mods_managers
        }


