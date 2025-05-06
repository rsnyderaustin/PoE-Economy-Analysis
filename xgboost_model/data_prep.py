import json
from pathlib import Path

from instances_and_definitions import ModifiableListing, ItemMod
from shared import PathProcessor
from . import utils


class DataPrep:

    def __init__(self):
        self.atype_map_json_path = (
            PathProcessor(Path.cwd())
            .attach_file_path_endpoint('data_exporting/exported_json_data_for_testing/atype_map.json')
            .path
        )

        with open(self.atype_map_json_path, 'r') as atype_map_file:
            self.atype_map_data = json.load(atype_map_file)

        self.btype_map_json_path = (
            PathProcessor(Path.cwd())
            .attach_file_path_endpoint('data_exporting/exported_json_data_for_testing/btype_map.json')
            .path
        )

        with open(self.btype_map_json_path, 'r') as btype_map_file:
            self.btype_map_data = json.load(btype_map_file)

        self.rarity_map_json_path = (
            PathProcessor(Path.cwd())
            .attach_file_path_endpoint('data_exporting/exported_json_data_for_testing/rarity_map.json')
            .path
        )

        with open(self.rarity_map_json_path, 'r') as rarity_map_file:
            self.rarity_map_data = json.load(rarity_map_file)

    def flatten_listing(self, listing: ModifiableListing):
        # Make a dict that averages out the property values if they're a range, otherwise just give us the number
        item_properties = {
            property_name: ((v[0] + v[1]) / 2) if v[0] and v[1] else v[0]
            for property_name, v in listing.item_properties.items()
        }
        flattened_data = {
            'date_fetched': listing.date_fetched,
            'btype': self.btype_map_data[listing.item_btype],
            'atype': self.atype_map_data[listing.item_atype],
            'rarity': self.rarity_map_data[listing.rarity],
            'ilvl': listing.ilvl,
            'corrupted': 1 if listing.corrupted else 0,
            **item_properties
        }

        summed_sub_mods = utils.sum_sub_mod_values(listing)
        # If you have a mod like "Adds 5 to 10 fire damage, 45% increased light radius", then we treat the
        # sub mod "Adds 5 to 10 fire damage" as its average (7.5). As of now I don't know of any sub mods with
        # multiple values where taking the average isn't applicable
        for sub_mod_id, value in summed_sub_mods.items():
            flattened_data[sub_mod_id] = value

        socketer_counts = utils.count_socketers(listing)
        for socketer_name, count in socketer_counts.items():
            flattened_data[socketer_name] = count

        for i, item_skill in enumerate(listing.item_skills):
            flattened_data[item_skill.name] = item_skill.level

        return flattened_data



