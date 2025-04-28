
import json
import logging
import requests

import craft_of_exile_api
from api_mediation.craft_of_exile_to_official_poe import CraftOfExileToOfficialPoe

logging.basicConfig(level=logging.INFO)

"""poe_api.StaticItemsToJson().execute()
poe_api.StatModifiersToJson().execute()"""

coe_puller = craft_of_exile_api.CraftOfExileDataPuller()
mods_data = coe_puller.pull_data(endpoint=craft_of_exile_api.Endpoint.MODS_AND_WEIGHTS)
base_data = coe_puller.pull_data(endpoint=craft_of_exile_api.Endpoint.BASE_TYPES)

with open("/Users/austinsnyder/Programming_application_projects/GitHub/PoE-Economy-Analysis/poe_api/json_data/stats.json", 'r') as f:
    official_mods_data = json.load(f)
    official_mods_data = {
        k: v for k, v in official_mods_data.items()
        if k in ['explicit']
    }

mods = [mod for mod in official_mods_data['explicit']
        if 'Energy Shield' in mod['text'] and 'Mana' in mod['text']]
coe_compiler = craft_of_exile_api.Compiler(mods_data=mods_data, bases_data=base_data)

coe_to_official = CraftOfExileToOfficialPoe(coe_compiler=coe_compiler,
                                            official_mod_data=official_mods_data)
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


