import json
import csv
import logging
import os
from pathlib import Path
import pandas as pd

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
            .attach_file_path_endpoint('xgboost_model/training_data/listings.json')
            .path
        )

        with open(self.training_data_json_path, 'r') as training_data_file:
            self.training_data = json.load(training_data_file)

        self.currency_to_exalts = utils.fetch_currency_to_conversion()

        self.num_rows = max(len(v_list) for v_list in self.training_data.values()) if self.training_data else 0

    def update_data(self):
        self.__init__()

    def _flatten_listing(self, listing: ModifiableListing):
        # Make a dict that averages out the property values if they're a range, otherwise just give us the number
        flattened_properties = dict()
        for property_name, property_values in listing.item_properties.items():
            flattened_properties[property_name] = 0
            for v in property_values:
                if isinstance(v, int) or isinstance(v, float):
                    flattened_properties[property_name] += v
                elif len(v) == 2:
                    flattened_properties[property_name] += ((v[0] + v[1]) / 2)
                elif len(v) == 1:
                    flattened_properties[property_name] += v[0]
                else:
                    raise ValueError(f"Property value {property_values} has unexpected structure.")

        if listing.price_currency in self.currency_to_exalts:
            exalts_price = listing.currency_amount * self.currency_to_exalts[listing.price_currency]
        elif listing.price_currency == 'exalted':
            exalts_price = listing.currency_amount
        else:
            raise ValueError(f"Currency {listing.price_currency} not supported.")

        flattened_data = {
            'minutes_since_listed': listing.minutes_since_listed,
            'minutes_since_league_start': listing.minutes_since_league_start,
            'exalts': exalts_price,
            'open_prefixes': listing.open_prefixes,
            'open_suffixes': listing.open_suffixes,
            'atype': self.atype_map_data[listing.item_atype],
            'rarity': self.rarity_map_data[listing.rarity],
            'corrupted': 1 if listing.corrupted else 0,
            **flattened_properties
        }

        summed_sub_mods = utils.sum_sub_mod_values(listing)
        # If you have a mod like "Adds 5 to 10 fire damage, 45% increased light radius", then we treat the
        # sub mod "Adds 5 to 10 fire damage" as its average (7.5). As of now I don't know of any sub mods with
        # multiple values where taking the average isn't applicable
        for col_name, value in summed_sub_mods.items():
            flattened_data[col_name] = value

        for i, item_skill in enumerate(listing.item_skills):
            flattened_data[item_skill.name] = item_skill.level

        return flattened_data

    def save_data(self, listings: list[ModifiableListing]):
        for listing in listings:
            flattened_data = self._flatten_listing(listing)

            for col_name, value in flattened_data.items():
                if col_name not in self.training_data:
                    # We have to insert a value for each row since this column has been added
                    self.training_data[col_name] = [None for _ in list(range(self.num_rows))]
                self.training_data[col_name].append(value)

            non_included_data_cols = [col for col in set(self.training_data.keys()) if col not in set(flattened_data.keys())]
            for col_name in non_included_data_cols:
                self.training_data[col_name].append(None)

            self.num_rows += 1

        logging.info(f"Writing {len(listings)} listings to training data.")

        shared_utils.write_to_file(file_path=self.training_data_json_path, data=self.training_data)



