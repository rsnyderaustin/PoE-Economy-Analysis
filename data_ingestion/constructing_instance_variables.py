import logging
import json

from shared import ATypeClassifier
import instances_and_definitions
from instances_and_definitions import ItemMod, ItemSocketer, ModClass, SubMod
from shared import shared_utils
from . import utils


def create_socketer_for_internal_storage(item_data: dict) -> ItemSocketer | None:
    """
    We can only determine socketer effects from items with only one socketer.
    """
    if ModClass.RUNE.value not in item_data:
        return None

    # We can only deterministically get rune data when there is one rune socketed, because different types of the same
    # data_ingesting can produce one rune text
    if len(item_data['socketedItems']) >= 2:
        logging.info(f"Item has more than one socketer. Skipping.")
        return None

    logging.info("Item only has one socketer. Creating rune.")

    rune_name = item_data['socketedItems'][0]['typeLine']
    rune_mod_text = item_data[ModClass.RUNE.value][0]

    # Rune mod text has this weird [text|text] format sometimes - the part after the pipe is all we need
    rune_mod_text = shared_utils.remove_piped_brackets(text=rune_mod_text)

    item_socketer = ItemSocketer(
        name=rune_name,
        text=rune_mod_text
    )
    return item_socketer


def _create_sub_mods(mod_id_to_sanitized_text: dict, mod_magnitudes: list) -> list[SubMod]:
    mod_ids = [
        magnitude['hash']
        for magnitude in mod_magnitudes
    ]

    sub_mods = []
    # Duplicate mod ID's in the 'extended' data only happen when an item mod has multiple ranges in the same mod.
    # Any duplicates are the same submod and so need to be combined
    duplicate_mod_ids = shared_utils.find_duplicate_values(mod_ids)
    for mod_id in duplicate_mod_ids:
        same_mod_magnitudes = [
            mod_magnitude
            for mod_magnitude in mod_magnitudes
            if mod_magnitude['hash'] == mod_id
        ]
        values_ranges = [
            [
                float(magnitude['min']) if 'min' in magnitude else None,
                float(magnitude['max']) if 'max' in magnitude else None
            ]
            for magnitude in same_mod_magnitudes
        ]
        sub_mod = SubMod(
            mod_id=mod_id,
            mod_text=mod_id_to_sanitized_text[mod_id],
            values_ranges=values_ranges
        )
        sub_mods.append(sub_mod)

    singleton_magnitudes = [magnitude
                            for magnitude in mod_magnitudes if magnitude['hash'] not in duplicate_mod_ids]
    for magnitude in singleton_magnitudes:
        mod_id = magnitude['hash']
        value_range = [
            float(magnitude['min']) if 'min' in magnitude else None,
            float(magnitude['max']) if 'max' in magnitude else None
        ]
        sub_mod = SubMod(
            mod_id=mod_id,
            mod_text=mod_id_to_sanitized_text[mod_id],
            values_ranges=value_range
        )
        sub_mods.append(sub_mod)

    return sub_mods


def create_item_mods(item_data: dict) -> list[ItemMod]:
    """
    'mods': {
        '#mod_class':
            #ItemMod1 (name, tier, magnitudes),
            #ItemMod2 (name, tier, magnitudes)
        '#mod_class:
            ...
    }
    """
    mods = []

    mod_class_enums = [e
                       for e in [
                           *instances_and_definitions.affixed_mod_classes,
                           *instances_and_definitions.non_affixed_mod_classes
                       ]
                       ]
    for mod_class_enum in mod_class_enums:
        mod_class = mod_class_enum.value
        if mod_class not in item_data:
            continue
        abbrev_class = utils.mod_class_to_abbrev[mod_class]
        mod_id_to_sanitized_text = utils.determine_mod_id_to_mod_text(
            mod_class=mod_class,
            item_data=item_data,
            sanitize_text=True
        )

        extended_mods_list = item_data['extended']['mods'][abbrev_class]

        # Each 'mod_data' represents data for an individual SubMod
        for mod_data in extended_mods_list:
            mod_name = mod_data['name']
            mod_tier = utils.determine_mod_tier(mod_data)
            affix_type = utils.determine_mod_affix_type(mod_data)

            sub_mods = _create_sub_mods(
                mod_id_to_sanitized_text=mod_id_to_sanitized_text,
                mod_magnitudes=mod_data['magnitudes']
            )

            item_mod = ItemMod(
                atype=ATypeClassifier.classify(item_data=item_data),
                mod_class=mod_class_enum,
                mod_name=mod_name,
                mod_affix_type=affix_type,
                mod_tier=mod_tier,
                sub_mods=sub_mods
            )

            mods.append(item_mod)

    return mods
