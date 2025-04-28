
import logging
import requests

import craft_of_exile_api

logging.basicConfig(level=logging.INFO)

"""poe_api.StaticItemsToJson().execute()
poe_api.StatModifiersToJson().execute()"""

coe_puller = craft_of_exile_api.CraftOfExileDataPuller()
mods_data = coe_puller.pull_data(endpoint=craft_of_exile_api.Endpoint.MODS_AND_WEIGHTS)
base_data = coe_puller.pull_data(endpoint=craft_of_exile_api.Endpoint.BASE_TYPES)

craft_of_exile_api.Compiler.compile(mods_data=weights_data, bases_data=base_data)
response = requests.get('https://www.craftofexile.com/data/affix.json')
data = response.json()
"""
corrupted_filter = query_classes.MetaModFilter(
    meta_mod_name_enum=ItemAttributes.MiscAttribute.CORRUPTED,
    mod_value='true'
)
meta_filters_group = poe_api.MetaFiltersGroup(
    search_type=poe_api.MetaSearchType.MISC,
    meta_mod_filters=[corrupted_filter]
)
query = poe_api.TradeQueryConstructor.create_trade_query(
    meta_filters_groups=[meta_filters_group]
)

response = poe_api.TradeItemFetcher.fetch_items(query=query)"""


