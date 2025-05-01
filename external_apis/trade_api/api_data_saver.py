
import json
import logging

from utils import PathProcessor
from .things import ItemListing, HybridMod, Mod, Rune


class ApiDataSaver:

    category_mods_path = PathProcessor.create_relative_file_path(
        endpoint='/external_apis/trade_api/json_data/item_category_mods.json'
    )
    with open(category_mods_path, 'r', encoding='utf-8') as json_file:
        category_mods_dict = json.load(json_file)

    rune_effects_path = PathProcessor.create_relative_file_path(
        endpoint='/external_apis/trade_api/json_data/rune_effects.json'
    )
    with open(rune_effects_path, 'r', encoding='utf-8') as json_file:
        rune_effects_dict = json.load(json_file)

    @classmethod
    def save_listing(cls, listing: ItemListing):
        if listing.item_btype not in cls.category_mods_dict:
            cls.category_mods_dict[listing.item_atype] = dict()

        for mod in listing.mods:
            if isinstance(mod, HybridMod):
                mod_ids = [sub_mod.mod_id for sub_mod in mod.mods]
                if mod.mod_name not in cls.category_mods_dict[listing.item_atype]:
                    logging.info(f"Found new hybrid mod {mod.mod_name} for item category {listing.item_atype}.")
                    cls.category_mods_dict[listing.item_atype][mod.mod_name] = mod_ids

            elif isinstance(mod, Mod):
                if mod.mod_name not in cls.category_mods_dict[listing.item_atype]:
                    logging.info(f"Found new mod {mod.mod_name} for item category {listing.item_atype}.")
                    cls.category_mods_dict[listing.item_atype][mod.mod_name] = mod.mod_id
            else:
                raise TypeError(f"Unrecognized mod type {type(mod)}.")

    @classmethod
    def save_runes(cls, item_btype: str, runes: list[Rune]):
        if item_btype not in cls.rune_effects_dict:
            cls.rune_effects_dict[item_btype] = dict()

        for rune in runes:
            cls.rune_effects_dict[item_btype][rune.rune_name] = rune.rune_effect

    @classmethod
    def export_data(cls):
        with open(cls.category_mods_path, "w") as f:
            json.dump(cls.category_mods_dict, f, indent=4)

        with open(cls.rune_effects_path, "w") as f:
            json.dump(cls.rune_effects_dict, f, indent=4)




