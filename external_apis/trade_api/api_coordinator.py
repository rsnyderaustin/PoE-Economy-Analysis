
import time

from .api_data_saver import ApiDataSaver
from .creators.runes_creator import RunesCreator
from .trade_items_fetcher import TradeItemsFetcher
from .querying import (MetaFiltersGroup, MetaModFilter, StatsFiltersGroup,
                       StatModFilter, TradeQueryConstructor)
from utils.enums import ItemCategory, MetaSearchType, MiscQueryAttribute, Rarity, ModClass
from .creators import ListingCreator


class TradeApiCoordinator:

    def __init__(self):
        self.api_data_saver = ApiDataSaver()
        self.api_data_fetcher = TradeItemsFetcher()

    def fill_internal_data(self):
        start_time = time.time()
        while time.time() - start_time < 10:
            rarity_filter = MetaModFilter(
                meta_attribute_enum=MiscQueryAttribute.RARITY,
                mod_value=Rarity.RARE.value
            )
            meta_filters_group = MetaFiltersGroup(
                search_type=MetaSearchType.TYPE,
                meta_mod_filters=[rarity_filter]
            )
            query = TradeQueryConstructor().create_trade_query(
                meta_filter_groups=[meta_filters_group]
            )

            api_items = self.api_data_fetcher.fetch_items(query=query)

            for item_response in api_items:
                if ModClass.RUNE.value in item_response['item']:
                    runes = RunesCreator.create_runes(item_response['item'])
                else:
                    continue

                if not runes:
                    continue

                self.api_data_saver.save_runes(
                    item_btype=item_response['item']['baseType'],
                    runes=runes
                )

        self.api_data_saver.export_data()


