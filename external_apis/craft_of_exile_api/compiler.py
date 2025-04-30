import ast
import logging

from .mod import CoEMod
from .mods_manager import CoEModsManager
from .mod_tier import CoEModTier


def _parse_mtypes_string(mtypes_string: str) -> list:
    if not mtypes_string:
        return []
    parsed = [part for part in mtypes_string.split('|') if part]
    return parsed


def _parse_nvalues(nvalues: str) -> tuple:
    # Safely evaluate the string to a Python object
    parsed = ast.literal_eval(nvalues)

    if not parsed:
        return None, None

    if isinstance(parsed[0], list):
        # [[a, b]] -> [a, b]
        return float(parsed[0][0]), float(parsed[0][1])
    else:
        # [a] -> a
        return float(parsed[0]), float(parsed[0])


class CoECompiler:

    # Base Types: Body Armour (DEX), Claw, Boots (Dex/Int), Crossbow, etc
    # Base Groups: Boots, Gloves, Body Armours, etc

    def __init__(self, mods_data: dict, bases_data: dict):
        self.mods_data = mods_data
        self.bases_data = bases_data

        btype_id_to_btype = bases_data['base']
        self.valid_btype_ids = set(btype_id_to_btype.keys())
        self.valid_btype_names = set(
            btype_id_to_btype[btype_id]
            for btype_id in self.valid_btype_ids
        )

        self.mod_id_to_mod_text = self.bases_data['mod']
        self.valid_coe_mod_ids = set(self.mod_id_to_mod_text.keys())
        self.valid_coe_mod_texts = set(self.mod_id_to_mod_text.values())

        self.mod_text_to_mod_id = {
            v: k
            for k, v in self.mod_id_to_mod_text.items()
        }

        base_group_id_to_base_group = self.bases_data['bgroup']
        self.btype_id_to_btype_name = self.bases_data['base']
        self.valid_btype_ids = set(self.btype_id_to_btype_name.keys())
        self.btype_name_to_mod_ids = {
            self.btype_id_to_btype_name[btype_id]: mod_ids
            for btype_id, mod_ids in self.mods_data['basemods'].items()
            if btype_id in self.valid_btype_ids
        }

        # Armour: ['5', '6', etc],
        # Weapons: ['11', '12', etc]
        self.item_class_to_socketable_ids = mods_data['socketables']['bybase']

        self.mod_id_to_affix_type = {
            mod_data_dict['id_modifier']: mod_data_dict['affix']
            for mod_data_dict in mods_data['modifiers']['seq']
        }

        # I think this right but not sure
        self.mod_type_id_to_mod_type = {
            mod_type_dict['id_mtype']: mod_type_dict['name_mtype']
            for mod_type_dict in mods_data['mtypes']['seq']
        }

        self.mod_id_to_mod_type_ids = {
            mod_data['id_modifier']: _parse_mtypes_string(mod_data['mtypes'])
            for mod_data in mods_data['modifiers']['seq']
        }

        self.mod_id_to_mod_types = {
            mod_id: [self.mod_type_id_to_mod_type[mod_type_id] for mod_type_id in mod_type_ids]
            for mod_id, mod_type_ids in self.mod_id_to_mod_type_ids.items()
        }

        self.mods_manager = self._fill_mods_manager()

        # This is just for testing - to show that mods do pair up correctly with their base types
        self.mod_name_to_btypes = {
            self.mod_id_to_mod_text[mod_id]: [self.btype_id_to_btype_name[btype_id]
                                              for btype_id in list(btypes.keys())
                                              if btype_id in self.btype_id_to_btype_name]
            for mod_id, btypes in self.mod_tiers_raw_data.items()
        }

    @property
    def mod_tiers_raw_data(self):
        return self.mods_data['tiers']

    @property
    def base_group_id_to_base_group(self):
        return self.bases_data['bgroup']

    @property
    def base_item_id_to_base_item_name(self):
        return self.bases_data['bitem']

    def mod_tiers_generator(self):
        btype_name_to_btype_id = {
            v: k
            for k, v in self.btype_id_to_btype_name.items()
        }

        for btype_id in self.valid_btype_ids:
            btype_name = self.btype_id_to_btype_name[btype_id]
            valid_mod_ids = self.btype_name_to_mod_ids[btype_name]
            for coe_mod_id in valid_mod_ids:
                tiers_data_list = self.mod_tiers_raw_data[coe_mod_id][btype_id]

                for tier_data in tiers_data_list:
                    yield CoEModTier(
                        btype_name=self.btype_id_to_btype_name[btype_id],
                        coe_mod_id=coe_mod_id,
                        ilvl=tier_data['ilvl'],
                        values_range=_parse_nvalues(tier_data['nvalues']),
                        weighting=tier_data['weighting']
                    )

    def _create_mods(self) -> list[CoEMod]:
        new_mods = list()
        mod_ids = set(self.mod_id_to_mod_text.keys())
        for mod_id in mod_ids:
            mod_text = self.mod_id_to_mod_text[mod_id]
            mod_types = self.mod_id_to_mod_types[mod_id]
            affix_type = self.mod_id_to_affix_type[mod_id]

            new_mod = CoEMod(
                coe_mod_text=mod_text,
                coe_mod_id=mod_id,
                mod_types=mod_types,
                affix_type=affix_type
            )
            new_mods.append(new_mod)

        return new_mods

    def _fill_mods_manager(self) -> CoEModsManager:
        mods_manager = CoEModsManager()
        mods = self._create_mods()

        for mod in mods:
            mods_manager.add_mod(mod=mod)

        return mods_manager
