
import logging
import re

from data_synthesizing.things.mods.mod import Mod
from external_apis.trade_api import helper_funcs
from utils.enums import ModAffixType, ModClass
from ..things import Mod


class ModsReturnable:

    def __init__(self,
                 implicit_mods: list[Mod],
                 enchant_mods: list[Mod],
                 fractured_mods: list[Mod],
                 rune_mods: list[Mod],
                 explicit_mods: list[Mod]):
        self.implicit_mods = implicit_mods
        self.enchant_mods = enchant_mods
        self.fracture_mods = fractured_mods
        self.rune_mods = rune_mods
        self.explicit_mods = explicit_mods


class ModsCreator:

    _mod_class_name_to_abbrev = {
        'implicitMods': 'implicit',
        'enchantMods': 'enchant',
        'explicitMods': 'explicit',
        'fracturedMods': 'fractured',
        'runeMods': 'rune'
    }

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
    def _determine_mod_tier(cls, mod_dict: dict) -> int:
        mod_tier = None
        if mod_dict['tier']:
            mod_tier_match = re.search(r'\d+', mod_dict['tier'])
            if mod_tier_match:
                mod_tier = mod_tier_match.group()
            else:
                logging.error(f"Did not find a tier number for item tier {mod_dict['tier']}")
                mod_tier = None
        return int(mod_tier) if mod_tier else None

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
    def _combine_mods(cls,
                      orig_mod: Mod,
                      new_values_range: tuple):
        orig_values_ranges = orig_mod.values_ranges
        if orig_values_ranges[-1] is None:
            new_values_ranges = orig_values_ranges[:-1] + (new_values_range,)
        else:
            new_values_ranges = orig_values_ranges + (new_values_range,)

        orig_mod.values_ranges = new_values_ranges

    @classmethod
    def create_mods(cls, item_data: dict) -> list:
        implicit_mods = ModsCreator.create_mods(it, ModClass.IMPLICIT) if 'implicitMods' in it else []
        explicit_mods = ModsCreator.create_mods(it, ModClass.EXPLICIT) if 'explicitMods' in it else []
        enchant_mods = ModsCreator.create_mods(it, ModClass.ENCHANT) if 'enchantMods' in it else []
        fractured_mods = ModsCreator.create_mods(it, ModClass.FRACTURED) if 'fracturedMods' in it else []
        rune_mods = ModsCreator.create_mods(it, ModClass.RUNE) if 'runeMods' in it else []

        """
            To create runes we need internal data on runes.
        """
        mod_classes = [e.value for e in ModClass if e != ModClass.RUNE]
        for mod_class in mod_classes:
        abbrev_mod_class = cls._mod_class_name_to_abbrev[mod_class.value]
        hashes_list = item_data['extended']['hashes'][abbrev_mod_class]

        mod_id_display_order = [
            mod_hash[0]
            for mod_hash in hashes_list
        ]
        mod_text_display_order = item_data[mod_class.value]
        mod_id_to_text = {
            mod_id: re.sub(r'\d+', '#', helper_funcs.remove_piped_brackets(mod_text))
            for mod_id, mod_text in list(zip(mod_id_display_order, mod_text_display_order))
        }

        # Rune mods don't have tier, affix type, etc
        if mod_class == ModClass.RUNE:
            rune_mods = []
            for mod_id in mod_id_display_order:
                mod_text = mod_id_to_text[mod_id]
                mod_values = helper_funcs.parse_values_from_mod_text(mod_text)
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

            processed_mods_by_id = dict()
            for magnitude in mod_data['magnitudes']:
                mod_id = magnitude['hash']

                # When a mod ID is present twice in a set of mod data, it's because the first mod represents the lower
                # value range, and the second mod represents the higher value range. So we just add data to the current mod
                # and skip this one
                if mod_id in processed_mods_by_id:
                    orig_mod = processed_mods_by_id[mod_id]
                    cls._combine_mods(orig_mod=orig_mod,
                                      new_values_range=cls._determine_mod_values_range(magnitude))
                    continue

                mod_text = mod_id_to_text.get(mod_id, "")

                # We wrap this in a tuple because sometimes mods have two ranges, and so there would be a second tuple to add
                # for that second range
                value_ranges = (cls._determine_mod_values_range(magnitude), None)
                mod_values = helper_funcs.parse_values_from_mod_text(mod_text)

                new_mod = Mod(
                    mod_class=mod_class,
                    mod_name=mod_name,
                    affix_type=affix_type,
                    mod_tier=mod_tier,
                    mod_values=mod_values,
                    mod_id=mod_id,
                    mod_text=mod_text,
                    values_ranges=value_ranges,
                )
                submods.append(new_mod)
                processed_mods_by_id[mod_id] = new_mod

            if len(submods) > 1:
                mods.append(HybridMod(mods=submods,
                                      mod_class=mod_class,
                                      affix_type=affix_type,
                                      mod_name=mod_name,
                                      mod_tier=mod_tier))
            else:
                mods.append(submods[0])

        return mods

