
import logging
import json
from pathlib import Path

from instances_and_definitions import ItemMod, ModifiableListing
from shared import PathProcessor, shared_utils


class ExportManager:

    def __init__(self):

        self.atype_mods_json_path = (
            PathProcessor(Path.cwd())
            .attach_file_path_endpoint('data_exporting/exported_json_data_for_testing/item_category_mods.json')
            .path
        )

        with open(self.atype_mods_json_path, 'r') as atype_mods_file:
            self.atype_mods_data = json.load(atype_mods_file)
            
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

        self.currency_map_json_path = (
            PathProcessor(Path.cwd())
            .attach_file_path_endpoint('data_exporting/exported_json_data_for_testing/currency_map.json')
            .path
        )

        with open(self.currency_map_json_path, 'r') as currency_map_file:
            self.currency_map_data = json.load(currency_map_file)

    def save_mod(self, item_mod: ItemMod):
        if item_mod.atype not in self.atype_mods_data:
            self.atype_mods_data[item_mod.atype] = dict()

        atype_dict = self.atype_mods_data[item_mod.atype]

        if item_mod.mod_id not in self.atype_mods_data[item_mod.atype]:
            atype_dict[item_mod.mod_id] = {
                'mod_class': item_mod.mod_class.value,
                'sub_mod_ids': [sub_mod.mod_id for sub_mod in item_mod.sub_mods],
                'mod_types': item_mod.mod_types,
                'mod_texts': [sub_mod.sanitized_mod_text for sub_mod in item_mod.sub_mods],
                'affix_type': item_mod.affix_type.value if item_mod.affix_type else None, # Some mods don't have affix types
                'mod_tiers': dict()
            }

        mod_tiers_dict = atype_dict[item_mod.mod_id]['mod_tiers']

        if str(item_mod.mod_ilvl) not in mod_tiers_dict:
            mod_id_to_values_ranges = {
                sub_mod.mod_id: sub_mod.values_ranges
                for sub_mod in item_mod.sub_mods
            }
            mod_tiers_dict[item_mod.mod_ilvl] = {
                    'ilvl': int(item_mod.mod_ilvl),
                    'mod_id_to_values_ranges': mod_id_to_values_ranges,
                    'weighting': item_mod.weighting
                }
            
    def aggregate_save_to_maps(self, listing: ModifiableListing) -> bool:
        """
        :return: True if data was saved and files were exported
        """
        should_export = False
        if listing.item_atype not in self.atype_map_data:
            self.atype_map_data[listing.item_atype] = len(self.atype_map_data)
            should_export = True

        if listing.item_btype not in self.btype_map_data:
            self.btype_map_data[listing.item_btype] = len(self.btype_map_data)
            should_export = True

        if listing.rarity not in self.rarity_map_data:
            self.rarity_map_data[listing.rarity] = len(self.rarity_map_data)
            should_export = True

        if listing.price_currency not in self.currency_map_data:
            self.currency_map_data[listing.price_currency] = len(self.currency_map_data)
            should_export = True

        if should_export:
            self.export_data()
            return True

        return False

    def export_data(self):
        logging.info("Exporting map data.")
        shared_utils.write_to_file(file_path=self.atype_mods_json_path, data=self.atype_mods_data)
        shared_utils.write_to_file(file_path=self.atype_map_json_path, data=self.atype_map_data)
        shared_utils.write_to_file(file_path=self.btype_map_json_path, data=self.btype_map_data)
        shared_utils.write_to_file(file_path=self.rarity_map_json_path, data=self.rarity_map_data)
        shared_utils.write_to_file(file_path=self.currency_map_json_path, data=self.currency_map_data)


