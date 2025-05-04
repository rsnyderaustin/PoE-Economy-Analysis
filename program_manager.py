
from data_exporting import ExportManager
from data_synthesizing import ATypeClassifier, ModsCreator, RunesCreator
import external_apis


class ProgramManager:

    def __init__(self):
        self.export_manager = ExportManager()

    def _fill_mods_file(self, api_item_response):
        mods = ModsCreator.create_mods(item_data=api_item_response)

    def execute(self):
        atype_classifier = ATypeClassifier()

        one_hand_mace_filter = external_apis.MetaFilter(
            meta_enum=external_apis.ItemCategory.ONE_HANDED_MACE
        )

        price_filter = external_apis.MetaFilter(
            meta_enum=external_apis.TradeFilters.PRICE,
            currency=external_apis.Currency.DIVINE_ORB,
            currency_amount=(1, 5)
        )

        rarity_filter = external_apis.MetaFilter(
            meta_enum=external_apis.Rarity.RARE
        )

        meta_mod_filters = [one_hand_mace_filter, price_filter, rarity_filter]
        query = external_apis.TradeQueryConstructor().create_trade_query(
            meta_mod_filters=meta_mod_filters
        )

        api_item_responses = external_apis.TradeItemsFetcher.fetch_items(query=query)

        for api_item_response in self.trade_coordinator.sample_items_generator():
            item_data = api_item_response['item']
            runes_for_internal_storage = RunesCreator.create_runes_for_internal_storage(
                item_data=item_data
            )
            item_atype = atype_classifier.convert(item_data=item_data)
            for rune in runes_for_internal_storage:
                self.export_manager.save_rune(atype=item_atype,
                                              rune=rune)


