
import logging
import json
from pathlib import Path

import rapidfuzz

from instances_and_definitions import ItemMod
from shared import PathProcessor
from . import utils


class PoecdMod:

    def __init__(self, mod_id: str):
        self.mod_id = mod_id

class ATypeDataManager:

    def __init__(self, atype_id: str, atype_name: str):
        self.atype_id = atype_id
        self.atype_name = atype_name

        self._mod_id_to_tiers_list = dict()
        self._mod_id_to_name = dict()

    @property
    def valid_mod_ids(self) -> set:
        return set(self._mod_id_to_tiers_list.keys())

    def insert_mod_tiers_list(self, mod_id: str, mod_name: str, tiers_list: list):
        self._mod_id_to_tiers_list[mod_id] = tiers_list
        self._mod_id_to_name[mod_id] = mod_name



class PoecdDataManager:

    def __init__(self):

        bases_path = (
            PathProcessor(Path.cwd())
            .attach_file_path_endpoint('testing_external_json_data/poecd_bases.json')
            .path
        )
        with open(bases_path, 'r') as f:
            self.bases_data = json.load(f)

        stats_path = (
            PathProcessor(Path.cwd())
            .attach_file_path_endpoint('testing_external_json_data/poecd_stats.json')
            .path
        )
        with open(stats_path, 'r') as f:
            self.stats_data = json.load(f)

        # Create AType data managers
        atype_id_to_atype_name = self.bases_data['base']
        valid_atype_ids = set(atype_id_to_atype_name.keys())

        self.atype_data_managers = dict()
        for atype_id in valid_atype_ids:
            atype_name = atype_id_to_atype_name[atype_id]
            new_data_manager = ATypeDataManager(
                atype_id=atype_id,
                atype_name=atype_name
            )
            self.atype_data_managers[atype_id] = new_data_manager

        # Fill AType data managers with Mod tiers data
        for mod_id, atype_dict in self.stats_data['tiers'].items():
            for atype_id, mod_tiers_list in atype_dict.items():
                atype_manager = self.atype_data_managers[atype_id]
                
                atype_manager.mod_id_to_tiers_list[mod_id] = mod_tiers_list

        self._mod_text_to_mod_id = {
            mod_text: mod_id
            for mod_id, mod_text in self.bases_data['mod'].items()
        }

        hybrid_mod_text_to_mod_id = {
            tuple(mod_text.split(',')): mod_id
            for mod_id, mod_text in self.bases_data['mod'].items()
            if ',' in mod_text
        }

        self._hybrid_mod_to_mod_ids = dict()
        for hybrid_mods, mod_id in hybrid_mod_text_to_mod_id.items():
            for hybrid_mod in hybrid_mods:
                hybrid_mod = hybrid_mod.strip()
                if hybrid_mod not in self._hybrid_mod_to_mod_ids:
                    self._hybrid_mod_to_mod_ids[hybrid_mod] = set()
                self._hybrid_mod_to_mod_ids[hybrid_mod].add(mod_id)

        self._atype_name_to_atype_id = {
            atype_name: atype_id
            for atype_id, atype_name in self.bases_data['base'].items()
        }

        mod_id_to_mod_type_ids = {
            mod_data['id_modifier']: utils.parse_poecd_mtypes_string(mod_data['mtypes'])
            for mod_data in self.stats_data['modifiers']['seq']
        }

        mod_type_id_to_mod_type = {
            mod_type_dict['id_mtype']: mod_type_dict['name_mtype']
            for mod_type_dict in self.stats_data['mtypes']['seq']
        }

        self._mod_id_to_mod_types = {
            mod_id: [mod_type_id_to_mod_type[mod_type_id] for mod_type_id in mod_type_ids]
            for mod_id, mod_type_ids in mod_id_to_mod_type_ids.items()
        }

        # BELOW ARE FOR TESTING PURPOSES ONLY

        # Some atypes are not yet implemented
        atype_id_to_atype_name = self.bases_data['base']

        self._atype_name_to_mod_ids = {
            atype_id_to_atype_name[atype_id]: mod_ids
            for atype_id, mod_ids in self.stats_data['basemods'].items()
            if atype_id in valid_atype_ids
        }

        mod_text_to_mod_types = {
            self.fetch_mod_text(mod_id): mod_types
            for mod_id, mod_types in self._mod_id_to_mod_types.items()
        }

    def fetch_valid_mod_ids(self, atype: str):
        return self._atype_name_to_mod_ids[atype]

    def fetch_valid_hybrid_mod_ids(self, atype: str):

    def hybrid_mod_texts(self, atype: str):
        return set(self._hybrid_mod_to_mod_ids.keys())

    def fetch_mod_id(self, atype: str, mod_text: str):
        key = self._generate_atype_mod_key(atype=atype,
                                           )
        return self._mod_text_to_mod_id[mod_text]

    def fetch_hybrid_mod_ids(self, hybrid_text: str):
        return self._hybrid_mod_to_mod_ids[hybrid_text]

    def fetch_mod_text(self, mod_id: str):
        return self.bases_data['mod'][mod_id]

    def fetch_mod_weighting(self, mod_id: str, atype: str, ilvl: int) -> int:
        atype_id = self._atype_name_to_atype_id[atype]
        mod_tiers_list = self.stats_data['tiers'][mod_id][atype_id]

        correct_mod_tier_dicts = [
            mod_tier for mod_tier in mod_tiers_list
            if mod_tier['ilvl'] == str(ilvl)
        ]
        if len(correct_mod_tier_dicts) >= 2:
            raise ValueError(f"Found multiple mod tiers with the same ilvl for Poecd mod {mod_id} and ilvl {ilvl}")
        elif len(correct_mod_tier_dicts) == 0:
            raise ValueError(f"Could not find mod tier with atype {str} and ilvl {ilvl}."
                             f"\nPoecd tiers data:\n{'\n'.join(mod_tiers_list)}")

        return int(correct_mod_tier_dicts[0]['weighting'])

    def fetch_mod_types(self, mod_id: str):
        return self._mod_id_to_mod_types[mod_id]


class ModPoecdDataInjecter:

    def __init__(self):

        self._coe_mod_match_replacements = {
            '# additional': 'an additional',
            'an additional': '# additional',
            'reduced': 'increased',
            'increased': 'reduced'
        }

        self._coe_mod_parts_to_remove = {
            '#% increased Waystones found in Area',
            '#% reduced Waystones found in Area'
        }

        self._poecd_manager = PoecdDataManager()

    def inject_poecd_data_into_mod(self, item_mod: ItemMod):
        poecd_mod_id = self._match_mod(item_mod)
        weighting = self._poecd_manager.fetch_mod_weighting(mod_id=poecd_mod_id,
                                                            atype=item_mod.atype,
                                                            ilvl=item_mod.mod_ilvl)
        item_mod.weighting = weighting

        mod_types = self._poecd_manager.fetch_mod_types(mod_id=poecd_mod_id)
        item_mod.mod_types = mod_types

    def _match_mod(self, item_mod: ItemMod) -> str | None:
        """

        :param item_mod:
        :return: The matching Poecd mod id.
        """

        if item_mod.is_hybrid:
            logging.info(f"\nHybrid mod match:\n")
            sub_mod_to_coe_mods = {
                sub_mod.mod_id: set()
                for sub_mod in item_mod.sub_mods
            }
            for sub_mod in item_mod.sub_mods:
                if sub_mod.mod_text in self._poecd_manager.hybrid_mod_texts:
                    poecd_mod_ids = self._poecd_manager.fetch_hybrid_mod_ids(sub_mod.mod_text)
                    sub_mod_to_coe_mods[sub_mod.mod_id] = poecd_mod_ids
                    logging.info(f"\tSubMod text {sub_mod.mod_text} possible mod matches:\n")
                    for poecd_mod_id in poecd_mod_ids:
                        logging.info(f"\t\t{self._poecd_manager.fetch_mod_text(poecd_mod_id)}")
                    continue

                matches = rapidfuzz.process.extract(sub_mod.mod_text,
                                                    self._poecd_manager.hybrid_mod_texts,
                                                    score_cutoff=95.0)

                logging.info(f"\tSubMod text {sub_mod.mod_text} possible mod matches:\n")
                for match, score, idx in matches:
                    coe_mod_id = self._poecd_manager.fetch_hybrid_mod_ids(match)
                    sub_mod_to_coe_mods[sub_mod.mod_id].add(coe_mod_id)
                    logging.info(f"\tSubMod text {sub_mod.mod_text} possible mod matches:\n")
                    logging.info(f"\t\t{self._poecd_manager.fetch_mod_text(match)}")
                logging.info("\n")

            matching_poecd_mod_id = set.intersection(
                *sub_mod_to_coe_mods.values()
            )
            if len(matching_poecd_mod_id) >= 2:
                logging.error(f"Found multiple matches for hybrid mod {item_mod.mod_id}")
                return

            logging.info(f"\tEnded up matching to {self._poecd_manager.fetch_mod_text(next(iter(matching_poecd_mod_id)))}")

        elif not item_mod.is_hybrid:

            match, score, idx = rapidfuzz.process.extractOne(item_mod.sub_mods[0].mod_text, self._poecd_manager.mod_texts)
            poecd_mod_id = self._poecd_manager.fetch_mod_id(match)
            logging.info(f"\nSingleton mod match: "
                         f"\n\tTrade mod: {item_mod.sub_mods[0].mod_text}:"
                         f"\n\tPoecd mod: {match}"
                         f"\n\tScore: {score}")
            return poecd_mod_id
