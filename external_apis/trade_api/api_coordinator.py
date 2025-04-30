from .api_data_saver import ApiDataSaver
from .trade_items_fetcher import TradeItemsFetcher
from .querying import (MetaFiltersGroup, MetaModFilter, StatsFiltersGroup,
                       StatModFilter, TradeQueryConstructor)
from utils.enums import MetaSearchType, MiscQueryAttribute, Rarity
from .listings import ListingsCreator


class TradeApiCoordinator:

    def __init__(self):
        self.api_data_loader = ApiDataSaver()
        self.api_data_fetcher = TradeItemsFetcher()

    def fill_internal_data(self):
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

        listings = ListingsCreator.create_listings(api_items_responses=api_items)
        x=0



