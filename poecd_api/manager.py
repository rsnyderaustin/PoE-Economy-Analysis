import logging

from shared import shared_utils
from file_management import FilesManager, DataPath
from .atype_manager_factory import AtypeManagerFactory
from .mods_management import GlobalPoecdAtypeModsManager
from .data_pull import PoecdDataPuller, PoecdEndpoint


class _PoecdSourceStore:
    def __init__(self, bases_data, stats_data):
        self.bases_data = bases_data
        self.stats_data = stats_data

        self._mod_id_to_text = bases_data['mod']
        self._mod_id_to_affix_type = self._build_mod_id_to_affix_type()
        self._atype_id_to_atype_name = bases_data['base']
        self.valid_atype_ids = set(self._atype_id_to_atype_name.keys())

        self._mod_id_to_mod_types = self._build_mod_id_to_mod_types()

    def _build_mod_id_to_affix_type(self) -> dict:
        return {
            mod_data_dict['id_modifier']: mod_data_dict['affix']
            for mod_data_dict in self.stats_data['modifiers']['seq']
        }

    @staticmethod
    def _determine_mod_types(mtypes_string: str) -> list:
        if not mtypes_string:
            return []
        parsed = [part for part in mtypes_string.split('|') if part]
        return parsed

    def _build_mod_id_to_mod_types(self) -> dict:
        mod_type_id_to_mod_type = {
            mod_type_dict['id_mtype']: mod_type_dict['name_mtype']
            for mod_type_dict in self.stats_data['mtypes']['seq']
        }

        mod_id_to_mod_type_ids = {
            mod_data['id_modifier']: self._determine_mod_types(mod_data['mtypes'])
            for mod_data in self.stats_data['modifiers']['seq']
        }

        return {
            mod_id: [mod_type_id_to_mod_type[mod_type_id] for mod_type_id in mod_type_ids]
            for mod_id, mod_type_ids in mod_id_to_mod_type_ids.items()
        }

    def fetch_mod_text(self, mod_id) -> str | None:
        return self._mod_id_to_text.get(mod_id, None)

    def fetch_affix_type(self, mod_id) -> str | None:
        return self._mod_id_to_affix_type.get(mod_id, None)

    def fetch_atype_name(self, atype_id) -> str | None:
        return self._atype_id_to_atype_name.get(atype_id, None)

    def fetch_mod_types(self, mod_id) -> str | None:
        return self._mod_id_to_mod_types.get(mod_id, None)


class PoecdDataManager:
    def __init__(self, refresh_data: bool, files_manager: FilesManager = None, data_puller: PoecdDataPuller = None):
        self.files_manager = files_manager or FilesManager()
        self.data_puller = data_puller or PoecdDataPuller()

        if refresh_data:
            self._refresh_and_fix_data()

        self.source_store = self._load_source_store_from_files()

    def _refresh_and_fix_data(self):
        bases_data = self.data_puller.pull_data(PoecdEndpoint.BASES)
        stats_data = self.data_puller.pull_data(PoecdEndpoint.STATS)

        self._fix_arrow_mods(bases_data, stats_data)

        self.files_manager.file_data[DataPath.POECD_BASES] = bases_data
        self.files_manager.file_data[DataPath.POECD_STATS] = stats_data

    def _load_source_store_from_files(self) -> _PoecdSourceStore:
        return _PoecdSourceStore(
            bases_data=self.files_manager.file_data[DataPath.POECD_BASES],
            stats_data=self.files_manager.file_data[DataPath.POECD_STATS]
        )

    def _fix_arrow_mods(self, bases_data: dict, stats_data: dict):
        """
        Merges duplicate bow mod variants into one mod with two tiers.
        """
        mod = bases_data.get('mod', {})
        if mod.get('5162') != "Bow Attacks fire # additional Arrows" or mod.get('5161') != "Bow Attacks fire an additional Arrow":
            logging.error("Arrow mod fix skipped: expected format not found.")
            return

        # Remove old mod
        mod.pop('5161', None)

        # Transfer its tier to the correct mod
        tier = stats_data['tiers'].get('5161', {}).get('20', [])[0]
        stats_data['tiers'].setdefault('5162', {}).setdefault('20', []).append(tier)

        # Remove 5161 everywhere else
        stats_data['tiers'].pop('5161', None)
        stats_data['modifiers']['seq'] = [m for m in stats_data['modifiers']['seq'] if m.get('id_modifier') != '5161']
        stats_data['modifiers']['ind'].pop('5161', None)
        stats_data['basemods']['20'] = [m for m in stats_data['basemods']['20'] if m != '5161']
        stats_data['modbases'].pop('5161', None)

    def build_global_mods_manager(self) -> GlobalPoecdAtypeModsManager:
        atype_managers = AtypeManagerFactory(self.source_store).build_mods_managers()
        global_manager = GlobalPoecdAtypeModsManager(atype_managers)
        return global_manager


