
from external_apis import TradeApiCoordinator
from data_synthesizing import ModsCreator, RunesCreator


class ProgramManager:

    def __init__(self):
        self.trade_coordinator = TradeApiCoordinator()

    def _fill_mods_file(self, api_item_response):
        mods = ModsCreator.create_mods(item_data=api_item_response)

    def execute(self):
        for api_item_response in self.trade_coordinator.sample_items_generator():
            runes_for_internal_storage = RunesCreator.create_runes_for_internal_storage(item_data=item_data)


