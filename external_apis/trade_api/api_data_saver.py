
import json

from utils import PathProcessor
from .listings import ItemListing


class ApiDataSaver:

    btype_mods_path = PathProcessor.create_relative_file_path(
        endpoint='/external_apis/trade_api/json_data/btype_mods.json'
    )
    with open(btype_mods_path, 'r', encoding='utf-8') as json_file:
        btype_mods_dict = json.load(json_file)

    def save_data(self, listing: ItemListing):
        pass

