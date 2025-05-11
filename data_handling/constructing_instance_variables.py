import logging

from data_handling.mod_matching.poecd_attribute_finder import PoecdAttributeFinder, PoecdModAttributes
from instances_and_definitions import ItemMod, ItemSocketer, ModClass, SubMod, ItemSkill, ModifiableListing
from shared import ATypeClassifier, shared_utils, trade_item_enums
from . import utils


class InstanceVariableConstructor:

    def __init__(self, poecd_attribute_finder: PoecdAttributeFinder):
        self.poecd_attribute_finder = poecd_attribute_finder

    def _create_duplicated_sub_mods(self, mod_id_to_text: dict, duplicate_mod_ids, mod_magnitudes):
        sub_mods = []
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
                actual_values=shared_utils.parse_values_from_text(mod_text),
                values_ranges=values_ranges
            )
            sub_mods.append(sub_mod)

        return sub_mods

    def _create_singleton_sub_mods(self, mod_id_to_text: dict, singleton_mod_ids, mod_magnitudes):
        singleton_magnitudes = [magnitude for magnitude in mod_magnitudes if magnitude['hash'] not in singleton_mod_ids]

        sub_mods = []
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
                actual_values=shared_utils.parse_values_from_text(mod_text),
                values_ranges=value_ranges
            )
            sub_mods.append(sub_mod)

        return sub_mods

    def _create_sub_mods(self, mod_id_to_text: dict, mod_magnitudes: list) -> list[SubMod]:
        mod_ids = [
            magnitude['hash']
            for magnitude in mod_magnitudes
        ]

        sub_mods = []
        # Duplicate mod ID's in the 'extended' data only happen when an item mod has multiple ranges in the same mod.
        # Any duplicates are the same submod and so need to be combined
        duplicate_mod_ids = shared_utils.find_duplicate_values(mod_ids)
        duplicated_sub_mods = self._create_duplicated_sub_mods(mod_id_to_text=mod_id_to_text,
                                                               duplicate_mod_ids=duplicate_mod_ids,
                                                               mod_magnitudes=mod_magnitudes)
        sub_mods.extend(duplicated_sub_mods)

        singleton_mod_ids = [mod_id for mod_id in mod_ids if mod_id not in duplicate_mod_ids]
        singleton_sub_mods = self._create_singleton_sub_mods(mod_id_to_text=mod_id_to_text,
                                                             singleton_mod_ids=singleton_mod_ids,
                                                             mod_magnitudes=mod_magnitudes)
        sub_mods.extend(singleton_sub_mods)

        return sub_mods

    def create_item_mod(self, mod_data: dict, mod_id_to_text: dict, mod_class: ModClass, atype: str):
        mod_name = mod_data['name']
        mod_tier = utils.determine_mod_tier(mod_data)
        mod_ilvl = mod_data['level']
        affix_type = utils.determine_mod_affix_type(mod_data)
        magnitudes = mod_data['magnitudes']

        sub_mods = self._create_sub_mods(
            mod_id_to_text=mod_id_to_text,
            mod_magnitudes=magnitudes
        )

        item_mod = ItemMod(
            atype=atype,
            mod_class=mod_class,
            mod_ilvl=mod_ilvl,
            mod_name=mod_name,
            affix_type=affix_type,
            mod_tier=mod_tier,
            sub_mods=sub_mods
        )

        poecd_attributes = self.poecd_attribute_finder.get_mod_attributes(item_mod=item_mod)
        item_mod.weighting = poecd_attributes.weighting
        item_mod.mod_types = poecd_attributes.mod_types

        return item_mod

    def create_skills(self, item_data: dict) -> list[ItemSkill]:
        if 'grantedSkills' not in item_data:
            return []

        skills = []

        for skill_data in item_data['grantedSkills']:
            raw_skill = skill_data['values'][0]

            # Spear Throw is the only skill that is granted by an item without a level. May have to update in the future
            if raw_skill[0] == 'Spear Throw':
                new_skill = ItemSkill(
                    name='Spear Throw'
                )
                skills.append(new_skill)
                continue

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

    def _parse_properties(self, item_data: dict) -> dict:
        properties = dict()
        if 'properties' in item_data:
            # The first property for an item is just its type group (ex: Body Armour, Boots, etc) - don't need that
            properties_list = item_data['properties'][1:]

            for property_data in properties_list:
                property_name = shared_utils.remove_piped_brackets(property_data['name'])

                if property_name == 'Elemental Damage':
                    # Elemental damage is a hybrid of the different elemental damage types
                    for property_value in property_data['values']:
                        if property_value[1] == 4:
                            properties['Fire Damage'] = shared_utils.parse_values_from_text(property_value[0])
                        elif property_value[1] == 5:
                            properties['Cold Damage'] = shared_utils.parse_values_from_text(property_value[0])
                        elif property_value[1] == 6:
                            properties['Lightning Damage'] = shared_utils.parse_values_from_text(property_value[1])
                    continue

                property_values = []
                for property_value in property_data['values']:
                    val = shared_utils.parse_values_from_text(property_value[0])
                    property_values.append(val)

                properties[property_name] = property_values

        return properties

    def _parse_requirements(self, item_data: dict):
        level_requirement = 0
        str_requirement = 0
        int_requirement = 0
        dex_requirement = 0

        properties = self._parse_properties(item_data)

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

    def create_listing(self,
                       api_item_response: dict,
                       item_mods: list[ItemMod]):
        item_data = api_item_response['item']
        listing_data = api_item_response['listing']
        minutes_since_listed = utils.determine_minutes_since(
            relevant_date=api_item_response['listing']['indexed']
        )
        # Gives minutes between league start and the item being listed
        minutes_since_league_start = utils.determine_minutes_since(
            relevant_date=utils.league_start_date,
            later_date=api_item_response['listing']['indexed']
        )

        if any([socketer_string in item_data['baseType'] for socketer_string in ['Rune', 'Talisman', 'Soul Core']]):
            logging.error(f"Received API item response for socketer. Skipping.")
            return

        level_requirement = 0
        str_requirement = 0
        int_requirement = 0
        dex_requirement = 0

        properties = self._parse_properties(item_data)

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

        socketers = []
        if 'runeMods' in item_data:
            for socketer_text in item_data['runeMods']:
                values = shared_utils.parse_values_from_text(socketer_text)
                sanitized_text = shared_utils.sanitize_mod_text(socketer_text)
                sanitized_text = shared_utils.remove_piped_brackets(sanitized_text)
                socketers.append(
                    ItemSocketer(
                        sanitized_socketer_text=sanitized_text,
                        actual_values=values
                    )
                )

        item_skills = create_skills(item_data)

        new_listing = ModifiableListing(
            listing_id=api_item_response['id'],
            date_fetched=shared_utils.today_date(),
            minutes_since_listed=minutes_since_listed,
            minutes_since_league_start=minutes_since_league_start,
            currency=listing_data['price']['currency'],
            currency_amount=listing_data['price']['amount'],
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
            socketers=socketers,
            item_properties=properties
        )
        return new_listing
