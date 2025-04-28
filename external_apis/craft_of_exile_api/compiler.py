import ast

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
        # Same id to same thing name
        self.base_type_id_to_base_type = bases_data['base']
        self.base_group_id_to_base_group = bases_data['bgroup']
        self.mod_id_to_mod_text = {
            mod_id: mod_text
            for mod_id, mod_text in bases_data['mod'].items()
        }
        self.base_item_id_to_base_item_name = bases_data['bitem']
        self.socketer_id_to_socketer_name = bases_data['socketable']

        # Same thing name to same id
        self.mod_text_to_mod_id = {v: k for k, v in self.mod_id_to_mod_text.items()}

        # Conversion
        self.base_type_id_to_mod_ids = mods_data['basemods']

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

        self.mod_text_to_mod_types = {
            self.mod_id_to_mod_text[mod_id]: mod_types
            for mod_id, mod_types in self.mod_id_to_mod_types.items()
        }

        self.mod_tiers_raw_data = mods_data['tiers']
        # self.base_type_mods_manager = BaseTypeModsManager(coe_tiers_data=mods_data['tiers'])

        self.mods_manager = self._fill_mods_manager()

    def _create_mods(self) -> list[CoEMod]:
        new_mods = list()
        mod_ids = set(self.mod_id_to_mod_text.keys())
        for mod_id in mod_ids:
            mod_text = self.mod_id_to_mod_text[mod_id]
            mod_types = self.mod_id_to_mod_types[mod_id]
            affix_type = self.mod_id_to_affix_type[mod_id]

            new_mod = CoEMod(
                mod_text=mod_text,
                mod_id=mod_id,
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

        # Fill the mods with their tier data
        tiered_mod_ids = set(self.mod_tiers_raw_data.keys())

        for mod_id in tiered_mod_ids:
            base_type_id_to_tiers_data = self.mod_tiers_raw_data[mod_id]
            for base_type_id, tiers_data_list in base_type_id_to_tiers_data.items():
                base_type_name = self.base_type_id_to_base_type[base_type_id]

                for tiers_data in tiers_data_list:
                    new_mod_tier = CoEModTier(
                        coe_mod_id=mod_id,
                        ilvl=tiers_data['ilvl'],
                        values_range=_parse_nvalues(tiers_data['nvalues']),
                        base_type=base_type_name
                    )

                    mods_manager.add_mod_tier(mod_tier=new_mod_tier)

        return mods_manager
