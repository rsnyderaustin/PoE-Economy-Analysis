
import json
from pathlib import Path

from data_synthesizing.things import Mod, Rune
from shared import PathProcessor


class ExportManager:

    def __init__(self):

        self.runes_json_path = (
            PathProcessor(Path.cwd())
            .attach_file_path_endpoint('internal_data/data_ingesting.txt')
            .path
        )

        with open(self.runes_json_path, 'r') as runes_file:
            self.runes_data = json.load(runes_file)

        self.atype_mods_json_path = (
            PathProcessor(Path.cwd())
            .attach_file_path_endpoint('internal_data/atype_mods.txt')
            .path
        )

        with open(self.atype_mods_json_path, 'r') as atype_mods_file:
            self.atype_mods_data = json.load(atype_mods_file)

    def save_mod(self, atype: str, mod_id: str, ):
        if mod.atype not in self.atype_mods_data:
            self.atype_mods_data[mod.atype] = dict()

        atype_dict = self.atype_mods_data[mod.atype]

        if mod.mod_id not in self.atype_mods_data[mod.atype]:
            atype_dict[mod.mod_id] = {
                'sub_mod_ids': [sub_mod.mod_id for sub_mod in mod.sub_mods],
                'mod_types': mod.mod_types,
                'mod_texts': [sub_mod.mod_text for sub_mod in mod.sub_mods],
                'affix_type': mod.affix_type.value,
                'mod_tiers': dict()
            }

            for ilvl, mod_tier in mod.ilvl_to_mod_tier.items():
                atype_dict[mod.mod_id]['mod_tiers'] = {
                    'ilvl': mod_tier.ilvl,
                    'mod_id_to_values_ranges': mod_tier.mod_id_to_values_ranges,
                    'weighting': mod_tier.weighting
                }

    def save_rune(self, atype: str, rune_name: str, rune_effect: str):
        if atype not in self.runes_data:
            self.runes_data[atype] = dict()

        if rune_name not in self.runes_data[atype]:
            self.runes_data[atype][rune_name] = rune_effect

    def export_data(self):
        with open(self.runes_json_path, 'w') as rune_file:
            json.dump(self.runes_data, rune_file, indent=4)


