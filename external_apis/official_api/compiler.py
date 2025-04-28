
import json
from pathlib import Path

from .mod import OfficialMod
from .mods_manager import OfficialModsManager


class OfficialCompiler:

    current_dir = Path(__file__).parent

    def __init__(self, static_data: dict, stats_data: dict):
        self.static_data = static_data
        self.stats_data = stats_data

        self.mods_manager = self._fill_mods_manager()

    def _create_official_mods(self) -> list[OfficialMod]:
        new_mods = list()
        for mod_class, mod_data_list in self.stats_data.items():
            for mod_data in mod_data_list:
                new_mod = OfficialMod(
                    mod_id=mod_data['id'],
                    mod_text=mod_data['text'],
                    mod_class=mod_data['type'] if 'type' in mod_data else None
                )

                new_mods.append(new_mod)

        return new_mods

    def _fill_mods_manager(self) -> OfficialModsManager:
        returnable_mods_manager = OfficialModsManager()
        mods = self._create_official_mods()
        for mod in mods:
            returnable_mods_manager.add_mod(mod=mod)

        return returnable_mods_manager


