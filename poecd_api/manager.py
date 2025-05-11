
from file_management import FilesManager, FileKey
from .atype_manager_factory import AtypeManagerFactory
from .data_management import PoecdSourceStore, PoecdAtypeManager, GlobalAtypesManager
from .data_pull import PoecdDataPuller, PoecdEndpoint


class PoecdManager:

    def __init__(self, refresh_data: bool):
        self.files_manager = FilesManager()
        self.source_store = self._create_poecd_source_store(refresh_data=refresh_data)

    def _create_poecd_source_store(self, refresh_data: bool):
        if refresh_data:
            self._refresh_data()

        poecd_source_store = PoecdSourceStore(bases_data=self.files_manager.file_data[FileKey.POECD_BASES],
                                              stats_data=self.files_manager.file_data[FileKey.POECD_STATS])

        return poecd_source_store

    def _refresh_data(self):
        data_puller = PoecdDataPuller()
        bases_data = data_puller.pull_data(PoecdEndpoint.BASES)
        self.files_manager.file_data[FileKey.POECD_BASES] = bases_data

        stats_data = data_puller.pull_data(PoecdEndpoint.STATS)
        self.files_manager.file_data[FileKey.POECD_STATS] = stats_data

    def create_global_atypes_manager(self) -> GlobalAtypesManager:
        atype_managers = AtypeManagerFactory(source_store=self.source_store).build_mods_managers()
        return GlobalAtypesManager(atype_managers=atype_managers)



