
from collections import Counter
import logging
import re

from external_apis.trade_api import utils
from shared.enums import ModAffixType, ModClass
from ..things.mods import Mod, SubMod, ModTier, TieredMod, SingletonMod
from shared import helper_funcs


def _sanitize_mod_text(mod_text: str):
    mod_text = re.sub(r'\d+', '#', mod_text)
    mod_text = helper_funcs.remove_piped_brackets(mod_text)
    return mod_text

def _determine_mod_affix_type(mod_dict: dict):
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


def _determine_mod_tier(mod_dict: dict) -> int:
    mod_tier = None
    if mod_dict['tier']:
        mod_tier_match = re.search(r'\d+', mod_dict['tier'])
        if mod_tier_match:
            mod_tier = mod_tier_match.group()
        else:
            logging.error(f"Did not find a tier number for item tier {mod_dict['tier']}")
            mod_tier = None
    return int(mod_tier) if mod_tier else None


def _determine_mod_ids(mod_dict: dict):
    mod_ids = [
        mod_magnitude_dict['hash']
        for mod_magnitude_dict in mod_dict['magnitudes']
    ]
    return mod_ids


def _determine_mod_values_range(mod_magnitude_dict: dict) -> tuple:
    if 'min' in mod_magnitude_dict and 'max' in mod_magnitude_dict:
        values_range = mod_magnitude_dict['min'], mod_magnitude_dict['max']
    else:
        value = next(v for k, v in mod_magnitude_dict.items() if k != 'hash')
        values_range = value, value

    return values_range


def _combine_mods(orig_mod: Mod,
                  new_values_range: tuple):
    orig_values_ranges = orig_mod.values_ranges
    if orig_values_ranges[-1] is None:
        new_values_ranges = orig_values_ranges[:-1] + (new_values_range,)
    else:
        new_values_ranges = orig_values_ranges + (new_values_range,)

        orig_mod.values_ranges = new_values_ranges


class ModsReturnable:

    def __init__(self,
                 implicit_mods: list[Mod] = None,
                 enchant_mods: list[Mod] = None,
                 fractured_mods: list[Mod] = None,
                 explicit_mods: list[Mod] = None):
        self.implicit_mods = implicit_mods or []
        self.enchant_mods = enchant_mods or []
        self.fracture_mods = fractured_mods or []
        self.explicit_mods = explicit_mods or []


class ModsCreator:

    _mod_class_name_to_abbrev = {
        'implicitMods': 'implicit',
        'enchantMods': 'enchant',
        'explicitMods': 'explicit',
        'fracturedMods': 'fractured',
        'runeMods': 'rune'
    }

    def __init__(self):
        self.item_data = dict()

    def _create_singleton_mod(self, mod_class: ModClass) -> SingletonMod:

    def _create_tiered_mod(self, mod_class: ModClass) -> TieredMod:
        abbrev_mod_class = self._mod_class_name_to_abbrev[mod_class.value]
        hashes_list = self.item_data['extended']['hashes'][abbrev_mod_class]

        mod_id_display_order = [mod_hash[0] for mod_hash in hashes_list]
        mod_text_display_order = self.item_data[mod_class.value]

        mod_id_to_sanitized_text = {
            mod_id: _sanitize_mod_text(mod_text)
            for mod_id, mod_text in list(zip(mod_id_display_order, mod_text_display_order))
        }

        extended_mods_data = self.item_data['extended']['mods'][abbrev_mod_class]

        # Each mod can have submods if it is hybrid
        for mod_data in extended_mods_data:
            mod_name = mod_data['name']
            affix_type = _determine_mod_affix_type(mod_data)
            mod_tier = _determine_mod_tier(mod_data)

            if len(mod_data['magnitudes']) == 1:
                only_mod_magnitude = mod_data['magnitudes'][0]
                mod_id = only_mod_magnitude['hash']
                sub_mod = SubMod(
                    mod_id=mod_id,
                    affix_type=affix_type,
                    mod_text=mod_id_to_sanitized_text[mod_id]
                )
                mod = TieredMod()
            magnitude_mod_ids = [
                magnitude['hash']
                for magnitude in mod_data['magnitudes']
            ]
            multi_range_mod_ids = helper_funcs.find_duplicate_values(magnitude_mod_ids)

    def create_mods(self, item_data: dict) -> list:

        self.item_data = item_data
        """
            To create data_ingesting we need internal data on data_ingesting.
        """
        mod_classes = [e.value for e in ModClass if e != ModClass.RUNE]
        for mod_class in mod_classes:

            mods = []
            for mod_data in extended_mods_data:

                submods = []

                processed_mods_by_id = dict()
                magnitude_mod_ids = [
                    magnitude['hash']
                    for magnitude in mod_data['magnitudes']
                ]
                multi_range_mod_ids = helper_funcs.find_duplicate_values(magnitude_mod_ids)
                for magnitude in mod_data['magnitudes']:
                    mod_id = magnitude['hash']

                    sub_mod = SubMod(
                        mod_id=mod_id,
                        affix_type=affix_type,
                        mod_text=mod_id_to_text[mod_id]
                    )

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
                        affix_type_enum=affix_type,
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

