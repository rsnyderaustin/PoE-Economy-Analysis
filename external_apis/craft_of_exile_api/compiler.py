from .coe_mod import CoEMod
from .mod_tier import ModTier
from .mods_manager import CoEModsManager


def _parse_mtypes_string(mtypes_string: str) -> list:
    if not mtypes_string:
        return []
    parsed = [part for part in mtypes_string.split('|') if part]
    return parsed


import ast


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

        self.btype_id_to_mod_ids = bases_data['basemods']

        self.btype_id_to_btype_name = bases_data['base']
        self.valid_btype_ids = set(self.btype_id_to_btype_name.keys())

        self.mod_id_to_mod_text = self.bases_data['mod']
        self.valid_coe_mod_ids = set(self.mod_id_to_mod_text.keys())
        self.raw_mod_tiers = self.mods_data['tiers']

        self.mods_manager = CoEModsManager()
        mods = self._create_mods()


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
                    yield ModTier(
                        btype_name=self.btype_id_to_btype_name[btype_id],
                        coe_mod_id=coe_mod_id,
                        ilvl=tier_data['ilvl'],
                        values_range=_parse_nvalues(tier_data['nvalues']),
                        weighting=tier_data['weighting']
                    )

    def _create_mods(self) -> list[CoEMod]:
        new_mods = list()
        for mod_id in self.mod_id_to_mod_text.keys():
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
