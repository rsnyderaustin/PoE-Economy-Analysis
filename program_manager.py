
from data_exporting import ExportManager
from data_synthesizing import ATypeClassifier, ModsCreator, RunesCreator
from external_apis import TradeApiCoordinator


class ProgramManager:

    def __init__(self):
        self.trade_coordinator = TradeApiCoordinator()
        self.export_manager = ExportManager()

    def _fill_mods_file(self, api_item_response):
        mods = ModsCreator.create_mods(item_data=api_item_response)

    def execute(self):
        atype_classifier = ATypeClassifier()
        for api_item_response in self.trade_coordinator.sample_items_generator():
            item_data = api_item_response['item']
            runes_for_internal_storage = RunesCreator.create_runes_for_internal_storage(
                item_data=item_data
            )
            item_atype = atype_classifier.convert(item_data=item_data)
            for rune in runes_for_internal_storage:
                self.export_manager.save_rune(atype=item_atype,
                                              rune=rune)


