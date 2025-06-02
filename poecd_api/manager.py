
from poe2db_scrape.mods_management import Poe2DbModsManager
from shared.logging import LogsHandler, LogFile
from .atype_manager_factory import AtypeManagerFactory
from .data_pull import PoecdDataPuller
from .internal_source_store import PoecdSourceStore

api_log = LogsHandler().fetch_log(LogFile.EXTERNAL_APIS)


def _convert_str_ints(obj):
    if isinstance(obj, dict):
        return {k: _convert_str_ints(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert_str_ints(elem) for elem in obj]
    elif isinstance(obj, str):
        # Fast and safe check for int-convertible strings
        if obj.isdigit() or (obj.startswith('-') and obj[1:].isdigit()):
            return int(obj)
    return obj


class PoecdDataManager:
    def __init__(self,
                 refresh_data: bool,
                 data_puller: PoecdDataPuller = None):
        self.data_puller = data_puller

        self.source_store = self._load_source_store_from_files()

    def _load_source_store_from_files(self) -> PoecdSourceStore:
        return PoecdSourceStore(
            bases_data=self.files_manager.fetch_data(DataPath.POECD_BASES, missing_ok=False),
            stats_data=self.files_manager.fetch_data(DataPath.POECD_STATS, missing_ok=False)
        )

    def _fix_arrow_mods(self, bases_data: dict, stats_data: dict):
        """
        Merges duplicate bow mod variants into one mod with two tiers.
        """
        mod = bases_data.get('mod', {})
        if mod.get('5162') != "Bow Attacks fire # additional Arrows" or mod.get('5161') != "Bow Attacks fire an additional Arrow":
            api_log.error("Arrow mod fix skipped: expected format not found.")
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

    def build_global_mods_manager(self) -> Poe2DbModsManager:
        atype_managers = AtypeManagerFactory(self.source_store).build_mods_managers()
        global_manager = Poe2DbModsManager(atype_managers)
        return global_manager


