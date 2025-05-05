
import json
from pathlib import Path

from instances_and_definitions import ItemMod, ItemSocketer
from shared import PathProcessor


class ExportManager:

    def __init__(self):

        self.runes_json_path = (
            PathProcessor(Path.cwd())
            .attach_file_path_endpoint('data_exporting/exported_json_data_for_testing/rune_effects.json')
            .path
        )

        with open(self.runes_json_path, 'r') as runes_file:
            self.runes_data = json.load(runes_file)

        self.atype_mods_json_path = (
            PathProcessor(Path.cwd())
            .attach_file_path_endpoint('data_exporting/exported_json_data_for_testing/item_category_mods.json')
            .path
        )

        with open(self.atype_mods_json_path, 'r') as atype_mods_file:
            self.atype_mods_data = json.load(atype_mods_file)

    def save_mod(self, item_mod: ItemMod):
        if item_mod.atype not in self.atype_mods_data:
            self.atype_mods_data[item_mod.atype] = dict()

        atype_dict = self.atype_mods_data[item_mod.atype]

        if item_mod.mod_id not in self.atype_mods_data[item_mod.atype]:
            atype_dict[item_mod.mod_id] = {
                'mod_class': item_mod.mod_class.value,
                'sub_mod_ids': [sub_mod.mod_id for sub_mod in item_mod.sub_mods],
                'mod_types': item_mod.mod_types,
                'mod_texts': [sub_mod.mod_text for sub_mod in item_mod.sub_mods],
                'affix_type': item_mod.affix_type.value if item_mod.affix_type else None, # Some mods don't have affix types
                'mod_tiers': dict()
            }

        mod_tiers_dict = atype_dict[item_mod.mod_id]['mod_tiers']

        if item_mod.mod_ilvl not in mod_tiers_dict:
            mod_id_to_values_ranges = {
                sub_mod.mod_id: sub_mod.values_ranges
                for sub_mod in item_mod.sub_mods
            }
            mod_tiers_dict[item_mod.mod_ilvl] = {
                    'ilvl': item_mod.mod_ilvl,
                    'mod_id_to_values_ranges': mod_id_to_values_ranges,
                    'weighting': item_mod.weighting
                }

    def save_socketer(self, atype: str, socketer: ItemSocketer):
        if atype not in self.runes_data:
            self.runes_data[atype] = dict()

        if socketer.name not in self.runes_data[atype]:
            self.runes_data[atype][socketer.name] = socketer.text

    def export_data(self):
        with open(self.runes_json_path, 'w') as rune_file:
            json.dump(self.runes_data, rune_file, indent=4)

        with open(self.atype_mods_json_path, 'w') as atype_file:
            json.dump(self.atype_mods_data, atype_file, indent=4)


