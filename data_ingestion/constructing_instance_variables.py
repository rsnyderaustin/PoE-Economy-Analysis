import logging

from external_apis import ItemCategory
from instances_and_definitions import ItemMod, ItemSocketer, ModClass, SubMod, ItemSkill, ModifiableListing
from shared import ATypeClassifier
from shared import shared_utils
from . import utils


def create_socketers(item_data: dict) -> list[ItemSocketer]:
    if 'socketedItems' not in item_data:
        return []

    socketers = []
    for socketer_data in item_data['socketedItems']:
        mods = [shared_utils.remove_piped_brackets(mod) for mod in socketer_data['explicitMods']]
        new_socketer = ItemSocketer(
            name=socketer_data['baseType'],
            mods=mods
        )
        socketers.append(new_socketer)

    return socketers

    """if ModClass.RUNE.value not in item_data:
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
    return item_socketer"""


def _create_sub_mods(mod_id_to_text: dict, mod_magnitudes: list) -> list[SubMod]:
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
            (
                float(magnitude['min']) if 'min' in magnitude else None,
                float(magnitude['max']) if 'max' in magnitude else None
            )
            for magnitude in same_mod_magnitudes
        ]
        mod_text = mod_id_to_text[mod_id]
        sanitized_text = shared_utils.sanitize_mod_text(mod_text)
        sub_mod = SubMod(
            mod_id=mod_id,
            sanitized_mod_text=sanitized_text,
            actual_values=shared_utils.parse_values_from_mod_text(mod_text),
            values_ranges=values_ranges
        )
        sub_mods.append(sub_mod)

    singleton_magnitudes = [magnitude
                            for magnitude in mod_magnitudes if magnitude['hash'] not in duplicate_mod_ids]
    for magnitude in singleton_magnitudes:
        mod_id = magnitude['hash']
        value_ranges = [
            (
                float(magnitude['min']) if 'min' in magnitude else None,
                float(magnitude['max']) if 'max' in magnitude else None
            )
        ]
        mod_text = mod_id_to_text[mod_id]
        sanitized_text = shared_utils.sanitize_mod_text(mod_text)
        sub_mod = SubMod(
            mod_id=mod_id,
            sanitized_mod_text=sanitized_text,
            actual_values=shared_utils.parse_values_from_mod_text(mod_text),
            values_ranges=value_ranges
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

    # Runes are created separately
    mod_class_enums = [e for e in ModClass if e != ModClass.RUNE]
    for mod_class_enum in mod_class_enums:
        mod_class = mod_class_enum.value
        if mod_class not in item_data:
            continue
        abbrev_class = utils.mod_class_to_abbrev[mod_class]
        mod_id_to_text = utils.determine_mod_id_to_mod_text(
            mod_class=mod_class,
            item_data=item_data,
            sanitize_text=False
        )

        extended_mods_list = item_data['extended']['mods'][abbrev_class]

        # Each 'mod_data' represents data for an individual SubMod
        for mod_data in extended_mods_list:
            mod_name = mod_data['name']
            mod_tier = utils.determine_mod_tier(mod_data)
            mod_ilvl = mod_data['level']
            affix_type = utils.determine_mod_affix_type(mod_data)
            magnitudes = mod_data['magnitudes']

            # As of right now this condition only applies to spears, which for some reason have a blank
            if not mod_name and not mod_tier and not affix_type and not magnitudes:
                continue
            else:
                sub_mods = _create_sub_mods(
                    mod_id_to_text=mod_id_to_text,
                    mod_magnitudes=magnitudes
                )

            item_mod = ItemMod(
                atype=ATypeClassifier.classify(item_data=item_data),
                mod_class=mod_class_enum,
                mod_ilvl=mod_ilvl,
                mod_name=mod_name,
                affix_type=affix_type,
                mod_tier=mod_tier,
                sub_mods=sub_mods
            )

            mods.append(item_mod)

    return mods


def create_skills(item_data: dict) -> list[ItemSkill]:
    if 'grantedSkills' not in item_data:
        return []

    skills = []

    raw_skill = item_data['grantedSkills']['values'][0]

    if isinstance(raw_skill, str):
        _, level_str, *skill_parts = raw_skill.split()
        level = int(level_str)
        skill_name = ' '.join(skill_parts)
    else:
        skill_name = raw_skill[0][0]
        level = raw_skill[0][1]

    new_skill = ItemSkill(
        name=skill_name,
        level=level
    )

    skills.append(new_skill)

    return skills


def create_listing(api_item_response: dict):
    item_data = api_item_response['item']
    listing_data = api_item_response['listing']

    # _clean_item_data(item_data)

    if any([rune_string in item_data['baseType'] for rune_string in ['Rune', 'Talisman', 'Soul Core']]):
        logging.error(f"Received API item response for socketer. Skipping.")
        return

    level_requirement = 0
    str_requirement = 0
    int_requirement = 0
    dex_requirement = 0

    properties = dict()
    if 'properties' in item_data:
        # The first property for an item is just its type group (ex: Body Armour, Boots, etc) - don't need that
        properties_list = item_data['properties'][1:]

        for property_data in properties_list:
            property_name = shared_utils.remove_piped_brackets(property_data['name'])

            if len(property_data['values']) >= 2:
                logging.error(f"{item_data}\nFound multiple values fields for item property from trade API. See data above.")

            property_values = shared_utils.parse_values_from_mod_text(property_data['values'][0][0])
            properties[property_name] = property_values

    if 'requirements' in item_data:
        for req_dict in item_data['requirements']:
            if req_dict['name'] == 'Level':
                level_requirement = int(req_dict['values'][0][0])
            if 'Str' in req_dict['name']:
                str_requirement = int(req_dict['values'][0][0])
            if 'Int' in req_dict['name']:
                int_requirement = int(req_dict['values'][0][0])
            if 'Dex' in req_dict['name']:
                dex_requirement = int(req_dict['values'][0][0])

    if 'properties' in item_data and 'name' in item_data['properties'][0]:
        atype = ATypeClassifier.classify(item_data=item_data)
    else:
        atype = item_data['baseType'] if 'baseType' in item_data else None

    socketer_names = []
    if 'socketedItems' in item_data:
        socketer_names = [socketer_data['baseType'] for socketer_data in item_data['socketedItems']]

    # Gems don't have mods
    item_mods = create_item_mods(item_data) if item_data['baseType'] != ItemCategory.ANY_GEM.value else []

    item_skills = create_skills(item_data)

    new_listing = ModifiableListing(
        listing_id=api_item_response['id'],
        date_fetched=listing_data['indexed'],
        price_currency=listing_data['price']['currency'],
        price_amount=listing_data['price']['amount'],
        item_name=item_data['name'],
        item_btype=item_data['baseType'] if 'baseType' in item_data else None,
        item_atype=atype,
        item_bgroup=item_data['properties'][0]['name'],
        rarity=item_data['rarity'] if 'rarity' in item_data else None,
        ilvl=item_data['ilvl'] if 'ilvl' in item_data else None,
        identified=item_data['identified'] if 'identified' in item_data else None,
        corrupted='corrupted' in item_data and item_data['corrupted'],
        level_requirement=level_requirement,
        str_requirement=str_requirement,
        int_requirement=int_requirement,
        dex_requirement=dex_requirement,
        implicit_mods=[mod for mod in item_mods if mod.mod_class == ModClass.IMPLICIT],
        enchant_mods=[mod for mod in item_mods if mod.mod_class == ModClass.ENCHANT],
        fractured_mods=[mod for mod in item_mods if mod.mod_class == ModClass.FRACTURED],
        explicit_mods=[mod for mod in item_mods if mod.mod_class == ModClass.EXPLICIT],
        item_skills=item_skills,
        socketers=socketer_names,
        item_properties=properties
    )
    return new_listing
