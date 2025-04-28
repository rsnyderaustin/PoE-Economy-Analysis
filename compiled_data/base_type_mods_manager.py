
import ast

from utils.enums import ModAffixType
from things.tiered_mod import TieredMod, ModTier


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


class BaseTypeModsManager:
    def __init__(self, coe_tiers_data: dict, coe_mod_id_to_mod_types: dict, coe_mod_id_to_affix_type: dict):
        self.data = self._build_data(coe_tiers_data=coe_tiers_data,
                                     coe_mod_id_to_mod_types=coe_mod_id_to_mod_types,
                                     coe_mod_id_to_affix_type=coe_mod_id_to_affix_type)

    def _convert_base_type(self, base_type: str = None, base_type_id: int = None):
        pass

    def fetch_modifiers(self, base_type: str, max_ilvl: int, mod_affix_type: ModAffixType, force_mod_type: str = None) -> list[ModTier]:
        base_type_id = self._convert_base_type(base_type=base_type)
        base_type_mod_data = self.data[base_type_id]

        if force_mod_type:
            base_type_mod_data = [
                mod_data for mod_data in self.data[base_type_id]
                if mod_data.mod_type == force_mod_type and mod_data.affix_type == mod_affix_type
            ]

        returnable_mods = [tiers_data
                           for mod_data in base_type_mod_data
                           for tiers_data in mod_data.fetch_modifiers(max_ilvl=max_ilvl)]

        return returnable_mods

    def _build_data(self,
                    coe_tiers_data: dict,
                    coe_mod_id_to_mod_types: dict,
                    coe_mod_id_to_affix_type) -> dict:
        data = dict()
        for mod_id, base_type_tiers_data in coe_tiers_data.items():
            for base_type_id, tiers_data_lists in base_type_tiers_data.items():
                if base_type_id not in data:
                    data[base_type_id] = dict()

                if mod_id not in data[base_type_id]:
                    data[base_type_id][mod_id] = TieredMod(
                        coe_mod_id=mod_id,
                        mod_types=coe_mod_id_to_mod_types[mod_id],
                        affix_type=coe_mod_id_to_affix_type[mod_id]
                    )

                for tier_data in tiers_data_lists:
                    data[base_type_id][mod_id].add_tier(
                        ilvl=int(tier_data['ilvl']),
                        values_range=_parse_nvalues(tier_data['nvalues']),
                        weighting=float(tier_data['weighting'])
                    )

        return data

