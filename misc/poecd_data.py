import json
from pathlib import Path

from data_synthesizing import utils
from instances_and_definitions import ModAffixType
from shared import PathProcessor


class PoecdMod:

    def __init__(self,
                 atype_id: str,
                 atype_name: str,
                 mod_id: int,
                 mod_text: str,
                 mod_types: list[str],
                 affix_type: ModAffixType,
                 tiers_list: list):
        self.atype_id = atype_id
        self.atype_name = atype_name
        self.mod_id = mod_id
        self.mod_text = mod_text

        self.mod_types = mod_types
        self.affix_type = affix_type

        self.ilvl_to_mod_tier = {
            tier_data['ilvl']: tier_data
            for tier_data in tiers_list
        }

    def fetch_weighting(self, ilvl: str):
        return self.ilvl_to_mod_tier[ilvl]['weighting']


class ATypeDataManager:

    def __init__(self,
                 atype_id: str,
                 atype_name: str,
                 mods: list[PoecdMod]):
        self.atype_id = atype_id
        self.atype_name = atype_name
        self.mods = mods

        self.mods_dict = {mod.mod_text: mod for mod in mods}
        self.mod_ids_dict = {mod.mod_id: mod for mod in mods}

        self.mods_affixed_dict = {
            ModAffixType.PREFIX: {mod.mod_text: mod for mod in mods if mod.affix_type == ModAffixType.PREFIX},
            ModAffixType.SUFFIX: {mod.mod_text: mod for mod in mods if mod.affix_type == ModAffixType.SUFFIX}
        }

        # This is useful for when we are matching mods to the Trade API data
        self.hybrid_parts_to_parent_dict = self.create_hybrid_to_parent_dict(mods=mods)
        self.hybrid_parts_to_parent_affixed_dict = {
            ModAffixType.PREFIX: self.create_hybrid_to_parent_dict(mods=mods, affix_type=ModAffixType.PREFIX),
            ModAffixType.SUFFIX: self.create_hybrid_to_parent_dict(mods=mods, affix_type=ModAffixType.SUFFIX)
        }
        self.num_hybrid_parts_dict = {
            mod.mod_id: len(mod.mod_text.split(','))
            for mod in mods
        }

        self.mod_id_to_affix_type = {mod.mod_id: mod.affix_type for mod in mods}
        self.mod_id_to_text = {mod.mod_id: mod.mod_text for mod in mods}
        self.mod_text_to_id = {v: k for k, v in self.mod_id_to_text.items()}

    @staticmethod
    def create_hybrid_to_parent_dict(mods, affix_type: ModAffixType = None) -> dict:
        hybrid_part_to_parent_id = dict()
        for mod in mods:
            if affix_type and mod.affix_type != affix_type:
                continue
            if ',' in mod.mod_text:
                hybrid_parts = [
                    part.strip()
                    for part in mod.mod_text.split(',')
                ]
                for part in hybrid_parts:
                    if part not in hybrid_part_to_parent_id:
                        hybrid_part_to_parent_id[part] = set()
                    hybrid_part_to_parent_id[part].add(mod.mod_id)
        return hybrid_part_to_parent_id


class PoecdDataManager:

    def __init__(self):
        self.bases_data = self._load_json_file('file_management/files/poecd_bases.json')
        self.stats_data = self._load_json_file('file_management/files/poecd_stats.json')

        self._normalize_data()

        self.mod_id_to_text = self.bases_data['mod']
        self.mod_id_to_affix_type = {
            mod_data_dict['id_modifier']: mod_data_dict['affix']
            for mod_data_dict in self.stats_data['modifiers']['seq']
        }
        self.atype_id_to_atype_name = self.bases_data['base']
        self.valid_atype_ids = set(self.atype_id_to_atype_name.keys())

        mod_type_id_to_mod_type = {
            mod_type_dict['id_mtype']: mod_type_dict['name_mtype']
            for mod_type_dict in self.stats_data['mtypes']['seq']
        }

        mod_id_to_mod_type_ids = {
            mod_data['id_modifier']: utils.parse_poecd_mtypes_string(mod_data['mtypes'])
            for mod_data in self.stats_data['modifiers']['seq']
        }

        self.mod_id_to_mod_types = {
            mod_id: [mod_type_id_to_mod_type[mod_type_id] for mod_type_id in mod_type_ids]
            for mod_id, mod_type_ids in mod_id_to_mod_type_ids.items()
        }

        mods = self._build_mods()
        self.atype_data_managers = dict()
        for atype_id in self.valid_atype_ids:
            atype_name = self.atype_id_to_atype_name[atype_id]
            self.atype_data_managers[atype_name] = ATypeDataManager(
                atype_id,
                atype_name,
                mods=[mod for mod in mods if mod.atype_id == atype_id]
            )

    def _load_json_file(self, relative_path):
        path = PathProcessor(Path.cwd()).attach_file_path_endpoint(relative_path).path
        with open(path, 'r') as f:
            return json.load(f)

    def _normalize_data(self):
        self.bases_data['base'] = {
            k: ('Quarterstaff' if v == 'Warstaff' else v)
            for k, v in self.bases_data['base'].items()
        }

    def _build_mods(self) -> list[PoecdMod]:

        socketer_mod_ids = {
            mod['id_modifier'] for mod in self.stats_data['modifiers']['seq']
            if mod['affix'] == 'socket'
        }

        atype_to_mods = dict()
        # Create tiers lists for mod creation in next block
        tiers_lists = dict()
        for mod_id, atype_dict in self.stats_data['tiers'].items():
            if mod_id in socketer_mod_ids:
                continue
            for atype_id, tiers_list in atype_dict.items():
                if atype_id not in self.valid_atype_ids:
                    continue

                if atype_id not in atype_to_mods:
                    atype_to_mods[atype_id] = set()
                atype_to_mods[atype_id].add(mod_id)

                if atype_id not in tiers_lists:
                    tiers_lists[atype_id] = dict()
                tiers_lists[atype_id][mod_id] = tiers_list

        # Create mods
        mods = list()
        for atype_id, mod_ids in atype_to_mods.items():
            for mod_id in mod_ids:
                mod_text = self.mod_id_to_text[mod_id]
                mod_types = self.mod_id_to_mod_types[mod_id]
                affix_type = self.mod_id_to_affix_type[mod_id]
                if affix_type and affix_type == 'prefix':
                    affix_type = ModAffixType.PREFIX
                elif affix_type and affix_type == 'suffix':
                    affix_type = ModAffixType.SUFFIX

                new_mod = PoecdMod(
                    atype_id=atype_id,
                    atype_name=self.atype_id_to_atype_name[atype_id],
                    mod_id=mod_id,
                    mod_text=mod_text,
                    mod_types=mod_types,
                    affix_type=affix_type,
                    tiers_list=tiers_lists[atype_id][mod_id]
                )
                mods.append(new_mod)

        return mods
