
import logging

import trade_api
from trade_api import *
from utils import ItemAttributes

logging.basicConfig(level=logging.INFO)


corrupted_filter = query_classes.MetaModFilter(
    meta_mod_name_enum=ItemAttributes.MiscAttribute.CORRUPTED,
    mod_value='true'
)
meta_filters_group = trade_api.MetaFiltersGroup(
    search_type=trade_api.MetaSearchType.MISC,
    meta_mod_filters=[corrupted_filter]
)
query = trade_api.TradeQueryConstructor.create_trade_query(
    meta_filters_groups=[meta_filters_group]
)

response = trade_api.TradeItemFetcher.fetch_items(query=query)
x=0
