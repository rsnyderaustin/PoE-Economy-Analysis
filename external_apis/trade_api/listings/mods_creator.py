
import logging
import re

from .hybrid_mod import HybridMod
from .mod import Mod
from utils.enums import ModAffixType, ModClass


class ModsCreator:

    _mod_class_name_to_abbrev = {
        'implicitMods': 'implicit',
        'enchantMods': 'enchant',
        'explicitMods': 'explicit',
        'fractureMods': 'fracture',
        'runeMods': 'rune'
    }

    @classmethod
    def _parse_values_from_mod_text(cls, mod_text: str) -> tuple:
        numbers = tuple(map(int, re.findall(r'\b\d+\b', mod_text)))
        return numbers

    @classmethod
    def _determine_mod_affix_type(cls, mod_dict: dict):
        mod_affix = None
        if mod_dict['tier']:
            first_letter = mod_dict['tier'][0]
            if first_letter == 'S':
                mod_affix = ModAffixType.SUFFIX
            elif first_letter == 'P':
                mod_affix = ModAffixType.PREFIX
            else:
                logging.error(f"Did not recognize first character as an affix type for "
                              f"item tier {mod_dict['tier']}")
                mod_affix = None

        return mod_affix

    @classmethod
    def _determine_mod_tier(cls, mod_dict: dict):
        mod_tier = None
        if mod_dict['tier']:
            mod_tier_match = re.search(r'\d+', mod_dict['tier'])
            if mod_tier_match:
                mod_tier = mod_tier_match.group()
            else:
                logging.error(f"Did not find a tier number for item tier {mod_dict['tier']}")
                mod_tier = None
        return mod_tier

    @classmethod
    def _determine_mod_ids(cls, mod_dict: dict):
        mod_ids = [
            mod_magnitude_dict['hash']
            for mod_magnitude_dict in mod_dict['magnitudes']
        ]
        return mod_ids

    @classmethod
    def _determine_mod_values_range(cls, mod_magnitude_dict: dict) -> tuple:
        if 'min' in mod_magnitude_dict and 'max' in mod_magnitude_dict:
            values_range = mod_magnitude_dict['min'], mod_magnitude_dict['max']
        else:
            value = next(v for k, v in mod_magnitude_dict.items() if k != 'hash')
            values_range = value, value

        return values_range

    @classmethod
    def create_mods(cls, item_data: dict, mod_class: ModClass) -> list:
        abbrev_mod_class = cls._mod_class_name_to_abbrev[mod_class.value]
        hashes_list = item_data['extended']['hashes'][abbrev_mod_class]

        mod_id_display_order = [
            mod_hash[0]
            for mod_hash in hashes_list
        ]
        mod_text_display_order = item_data[mod_class.value]
        mod_id_to_text = {
            mod_id: mod_text
            for mod_id, mod_text in list(zip(mod_id_display_order, mod_text_display_order))
        }

        if mod_class == ModClass.RUNE:
            rune_mods = []
            for mod_id in mod_id_display_order:
                mod_text = mod_id_to_text[mod_id]
                mod_values = cls._parse_values_from_mod_text(mod_text)
                rune_mod = Mod(
                    mod_class=mod_class,
                    mod_id=mod_id,
                    mod_text=mod_text,
                    mod_values=mod_values
                )
                rune_mods.append(rune_mod)

            return rune_mods

        extended_mods_data = item_data['extended']['mods'][abbrev_mod_class]

        mods = []
        for mod_data in extended_mods_data:
            mod_name = mod_data['name']
            affix_type = cls._determine_mod_affix_type(mod_data)
            mod_tier = cls._determine_mod_tier(mod_data)

            submods = []

            # Magnitudes are not included for implicit mods
            if mod_class == ModClass.IMPLICIT:
                new_mod = Mod(

                )
            for magnitude in mod_data['magnitudes']:
                mod_id = magnitude['hash']
                mod_text = mod_id_to_text.get(mod_id, "")
                value_ranges = cls._determine_mod_values_range(magnitude)
                mod_values = cls._parse_values_from_mod_text(mod_text)

                submods.append(Mod(
                    mod_class=mod_class,
                    mod_name=mod_name,
                    affix_type=affix_type,
                    mod_tier=mod_tier,
                    mod_values=mod_values,
                    mod_id=mod_id,
                    mod_text=mod_text,
                    value_ranges=value_ranges,
                ))

            if len(submods) > 1:
                mods.append(HybridMod(mod_class=mod_class, mods=submods))
            else:
                mods.append(submods[0])

        return mods

