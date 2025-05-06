import json
import csv
import logging
import os
from pathlib import Path

from instances_and_definitions import ModifiableListing, ItemMod
from shared import PathProcessor, shared_utils
from . import utils


class DataPrep:

    def __init__(self):
        atype_map_json_path = (
            PathProcessor(Path.cwd())
            .attach_file_path_endpoint('data_exporting/exported_json_data_for_testing/atype_map.json')
            .path
        )

        with open(atype_map_json_path, 'r') as atype_map_file:
            self.atype_map_data = json.load(atype_map_file)

        btype_map_json_path = (
            PathProcessor(Path.cwd())
            .attach_file_path_endpoint('data_exporting/exported_json_data_for_testing/btype_map.json')
            .path
        )

        with open(btype_map_json_path, 'r') as btype_map_file:
            self.btype_map_data = json.load(btype_map_file)

        rarity_map_json_path = (
            PathProcessor(Path.cwd())
            .attach_file_path_endpoint('data_exporting/exported_json_data_for_testing/rarity_map.json')
            .path
        )

        with open(rarity_map_json_path, 'r') as rarity_map_file:
            self.rarity_map_data = json.load(rarity_map_file)

        currency_map_json_path = (
            PathProcessor(Path.cwd())
            .attach_file_path_endpoint('data_exporting/exported_json_data_for_testing/currency_map.json')
            .path
        )

        with open(currency_map_json_path, 'r') as currency_map_file:
            self.currency_map_data = json.load(currency_map_file)

        self.training_data_json_path = (
            PathProcessor(Path.cwd())
            .attach_file_path_endpoint('xgboost_model/test_training_data.json')
            .path
        )

        with open(self.training_data_json_path, 'r') as training_data_file:
            self.training_data = json.load(training_data_file)

        self.num_rows = len(self.training_data)

    def update_data(self):
        self.__init__()

    def flatten_listing(self, listing: ModifiableListing):
        # Make a dict that averages out the property values if they're a range, otherwise just give us the number
        flattened_properties = dict()
        for property_name, property_values in listing.item_properties.items():
            # My understanding is that a property only ever has more than one value when its describing Elemental Damage
            if property_name != 'Elemental Damage' and len(property_values) >= 2:
                logging.error(f"Property name {property_name} has more than one value and is not 'Elemental Damage' as expected.")

            flattened_properties[property_name] = 0
            for v in property_values:
                val = ((v[0] + v[1]) / 2) if len(v) >= 2 else v[0]
                flattened_properties[property_name] += val

        flattened_data = {
            'listing_id': listing.listing_id,
            'date_fetched': listing.date_fetched,
            'days_since_listed': listing.days_since_listed,
            'currency': self.currency_map_data[listing.price_currency],
            'currency_amount': listing.currency_amount,
            'open_prefixes': listing.open_prefixes,
            'open_suffixes': listing.open_suffixes,
            'btype': self.btype_map_data[listing.item_btype],
            'atype': self.atype_map_data[listing.item_atype],
            'rarity': self.rarity_map_data[listing.rarity],
            'ilvl': listing.ilvl,
            'corrupted': 1 if listing.corrupted else 0,
            **flattened_properties
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

        for col_name, value in flattened_data.items():
            if col_name not in self.training_data:
                # We have to insert a value for each row since this column has been added
                self.training_data[col_name] = [None for _ in list(range(self.num_rows))]
            self.training_data[col_name].append(value)

        non_included_data_cols = [col for col in set(self.training_data.keys()) if col not in set(flattened_data.keys())]
        for col_name in non_included_data_cols:
            self.training_data[col_name].append(None)

        self.num_rows += 1

        shared_utils.write_to_file(file_path=self.training_data_json_path, data=self.training_data)

        return flattened_data



