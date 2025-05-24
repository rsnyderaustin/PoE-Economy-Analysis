import logging

from .attribute_finder import PoecdAttributeFinder
from file_management import FilesManager, DataPath
from .atype_manager_factory import AtypeManagerFactory
from .data_management import PoecdSourceStore, GlobalAtypesManager
from .data_pull import PoecdDataPuller, PoecdEndpoint


class PoecdManager:

    def __init__(self, refresh_data: bool):
        self.files_manager = FilesManager()
        self.source_store = self._create_poecd_source_store(refresh_data=refresh_data)

    def _create_poecd_source_store(self, refresh_data: bool):
        if refresh_data:
            self._refresh_data()

        poecd_source_store = PoecdSourceStore(bases_data=self.files_manager.file_data[DataPath.POECD_BASES],
                                              stats_data=self.files_manager.file_data[DataPath.POECD_STATS])

        return poecd_source_store

    def _refresh_data(self):
        data_puller = PoecdDataPuller()
        bases_data = data_puller.pull_data(PoecdEndpoint.BASES)
        stats_data = data_puller.pull_data(PoecdEndpoint.STATS)
        self._fix_data(bases_data=bases_data,
                       stats_data=stats_data)

        self.files_manager.file_data[DataPath.POECD_BASES] = bases_data
        self.files_manager.file_data[DataPath.POECD_STATS] = stats_data

    def _fix_data(self, bases_data: dict, stats_data: dict):

        """
        This currently only fixes a case where separate 'additional arrow' bow mods in Poecd API should be just one single mod with 2 tiers.
        """
        first_cond = '5162' in bases_data['mod'] and bases_data['mod']['5162'] == "Bow Attacks fire # additional Arrows"
        second_cond = '5161' in bases_data['mod'] and bases_data['mod']['5161'] == "Bow Attacks fire an additional Arrow"

        if not first_cond or not second_cond:
            logging.error("Bow attacks additional arrow fix in Poecd API manager has been changed in some way. Maybe fixed?")
            return

        bases_data['mod'].pop('5161')

        stat_to_pop = stats_data['tiers']['5161']['20'][0]
        stats_data['tiers']['5162']['20'].append(stat_to_pop)
        stats_data['tiers'].pop('5161')

        stats_data['modifiers']['seq'] = [
            mod_dict for mod_dict in stats_data['modifiers']['seq'] if mod_dict['id_modifier'] != '5161'
        ]
        stats_data['modifiers']['ind'].pop('5161')
        stats_data['basemods']['20'] = [mod_id for mod_id in stats_data['basemods']['20'] if mod_id != '5161']
        stats_data['modbases'].pop('5161')

    def build_attributes_finder(self) -> PoecdAttributeFinder:
        atype_managers = AtypeManagerFactory(source_store=self.source_store).build_mods_managers()
        global_manager = GlobalAtypesManager(atype_managers=atype_managers)
        return PoecdAttributeFinder(global_manager)


