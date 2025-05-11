
from file_management import FilesManager, FileKey
from .data_management import PoecdSourceStore, GlobalAtypesManager, PoecdAtypeManager, PoecdMod
from .data_pull import PoecdDataPuller, PoecdEndpoint


class PoecdManager:

    def __init__(self, refresh_data: bool):
        self.files_manager = FilesManager()
        self.source_store = self._create_poecd_source_store(refresh_data=refresh_data)

        self.global_atypes_manager = self._create_global_atypes_manager()

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

    def _create_tiers_data(self):
        socketer_mod_ids = {
            mod['id_modifier'] for mod in self.source_store.stats_data['modifiers']['seq']
            if mod['affix'] == 'socket'
        }

        tiers_data = {
            mod_id: atype_data for mod_id, atype_data in self.source_store.stats_data['tiers'].items()
            if mod_id not in socketer_mod_ids
        }

        return tiers_data

    def _create_global_atypes_manager(self) -> GlobalAtypesManager:
        tiers_data = self._create_tiers_data()

        # Create each individual AtypeManager

        global_atypes_manager = GlobalAtypesManager(atypes_managers=atypes_managers)

        # Create each mod, and pass it to the GlobalAtypesManager
        inputs = [
            (mod_id, atype_id)
            for mod_id, atype_dict in tiers_data.items()
            for atype_id in atype_dict.keys()
        ]
        for mod_id, atype_id in inputs:
            new_mod = PoecdMod(atype_id=atype_id,
                               atype_name=self.source_store.fetch_atype_name(atype_id),
                               mod_id=mod_id)
            global_atypes_manager.add_mod(mod=new_mod)

        # Iterate through each mod tier, passing it into GlobalAtypesManager
        inputs = [
            (mod_id, atype_id, tiers_list)
            for mod_id, atype_dict in tiers_data.items()
            for atype_id, tiers_list in atype_dict.items()
            if atype_id in self.source_store.valid_atype_ids
        ]
        for mod_id, atype_id, tiers_list in inputs:
            global_atypes_manager.add_mod_tier(atype_id=atype_id,
                                               mod_id=mod_id,
                                               tiers_list=tiers_list)



