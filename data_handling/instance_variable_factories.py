import logging

from instances_and_definitions import ItemMod, ItemSocketer, ModClass, SubMod, ItemSkill, ModifiableListing
from shared import ATypeClassifier, shared_utils
from . import utils
from .mods.poecd_attribute_finder import PoecdAttributeFinder


class ModFactory:

    def __init__(self, poecd_attribute_finder: PoecdAttributeFinder):
        self.poecd_attribute_finder = poecd_attribute_finder

    @staticmethod
    def _create_duplicated_sub_mods(mod_id_to_text: dict, duplicate_mod_ids, mod_magnitudes):
        sub_mods = []
        for mod_id in duplicate_mod_ids:
            same_mod_magnitudes = [
                mod_magnitude
                for mod_magnitude in mod_magnitudes
                if mod_magnitude['hash'] == mod_id
            ]
            values_ranges = [
                (
                    utils.convert_string_into_number(magnitude['min']) if 'min' in magnitude else None,
                    utils.convert_string_into_number(magnitude['max']) if 'max' in magnitude else None
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

    @staticmethod
    def _create_singleton_sub_mods(mod_id_to_text: dict, singleton_mod_ids, mod_magnitudes) -> list[SubMod]:
        singleton_magnitudes = [magnitude for magnitude in mod_magnitudes if magnitude['hash'] in singleton_mod_ids]

        sub_mods = []
        for magnitude in singleton_magnitudes:
            mod_id = magnitude['hash']
            value_ranges = [
                (
                    utils.convert_string_into_number(magnitude['min']) if 'min' in magnitude else None,
                    utils.convert_string_into_number(magnitude['max']) if 'max' in magnitude else None
                )
            ]
            mod_text = mod_id_to_text[mod_id]
            actual_values = shared_utils.parse_values_from_text(mod_text)

            if len(actual_values) != len(value_ranges):
                raise ValueError(f"Item has a different number of ranges and actual values:"
                                 f"\n\tRanges: {value_ranges}"
                                 f"\n\tActual values: {actual_values}")

            sanitized_text = shared_utils.sanitize_mod_text(mod_text)
            sub_mod = SubMod(
                mod_id=mod_id,
                sanitized_mod_text=sanitized_text,
                actual_values=shared_utils.parse_values_from_text(mod_text),
                values_ranges=value_ranges
            )
            sub_mods.append(sub_mod)

        return sub_mods

    @classmethod
    def _create_sub_mods(cls, mod_id_to_text: dict, mod_magnitudes: list) -> list[SubMod]:
        mod_ids = [
            magnitude['hash']
            for magnitude in mod_magnitudes
        ]

        sub_mods = []
        # Duplicate mod ID's in the 'extended' data only happen when an item mod has multiple ranges in the same mod.
        # Any duplicates are the same submod and so need to be combined
        duplicate_mod_ids = shared_utils.find_duplicate_values(mod_ids)
        duplicated_sub_mods = cls._create_duplicated_sub_mods(mod_id_to_text=mod_id_to_text,
                                                              duplicate_mod_ids=duplicate_mod_ids,
                                                              mod_magnitudes=mod_magnitudes)
        sub_mods.extend(duplicated_sub_mods)

        singleton_mod_ids = [mod_id for mod_id in mod_ids if mod_id not in duplicate_mod_ids]
        singleton_sub_mods = cls._create_singleton_sub_mods(mod_id_to_text=mod_id_to_text,
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
            mod_class_e=mod_class,
            mod_ilvl=mod_ilvl,
            mod_name=mod_name,
            affix_type_e=affix_type,
            mod_tier=mod_tier,
            sub_mods=sub_mods
        )

        poecd_attributes = self.poecd_attribute_finder.get_poecd_mod_attributes(item_mod=item_mod)
        if poecd_attributes:  # returns None if
            item_mod.weighting = poecd_attributes.weighting
            item_mod.mod_types = poecd_attributes.mod_types

        return item_mod


class SkillsFactory:

    @staticmethod
    def create_skills(item_data: dict) -> list[ItemSkill]:
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


class ListingFactory:

    @staticmethod
    def _parse_properties(item_data: dict) -> dict:
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

    @staticmethod
    def _parse_requirements(item_data: dict) -> dict:
        requirements = {
            'level_requirement': 0,
            'str_requirement': 0,
            'int_requirement': 0,
            'dex_requirement': 0
        }

        if 'requirements' in item_data:
            for req_dict in item_data['requirements']:
                if req_dict['name'] == 'Level':
                    requirements['level_requirement'] = int(req_dict['values'][0][0])
                if 'Str' in req_dict['name']:
                    requirements['str_requirement'] = int(req_dict['values'][0][0])
                if 'Int' in req_dict['name']:
                    requirements['int_requirement'] = int(req_dict['values'][0][0])
                if 'Dex' in req_dict['name']:
                    requirements['dex_requirement'] = int(req_dict['values'][0][0])

        return requirements

    @staticmethod
    def _parse_socketers(item_data: dict) -> list[ItemSocketer]:
        socketers = []

        if 'runeMods' not in item_data:
            return []

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
        return socketers

    @staticmethod
    def _determine_atype(item_data: dict) -> str:
        if 'properties' in item_data and 'name' in item_data['properties'][0]:
            atype = ATypeClassifier.classify(item_data=item_data)
        else:
            atype = item_data['baseType'] if 'baseType' in item_data else None

        return atype

    @staticmethod
    def _item_is_socketer(item_data: dict):
        return any([socketer_string in item_data['baseType'] for socketer_string in ['Rune', 'Talisman', 'Soul Core']])

    @classmethod
    def create_listing(cls,
                       api_item_response: dict,
                       item_mods: list[ItemMod]) -> ModifiableListing | None:
        item_data = api_item_response['item']
        listing_data = api_item_response['listing']

        if cls._item_is_socketer(item_data):
            logging.error(f"Received create_listing request for socketer. Skipping.")
            return

        listing_date = api_item_response['listing']['indexed']
        minutes_since_listed = utils.determine_minutes_since(
            relevant_date=listing_date
        )
        minutes_since_league_start = utils.determine_minutes_since(
            relevant_date=utils.league_start_date,
            later_date=listing_date
        )

        properties = cls._parse_properties(item_data)
        reqs = cls._parse_requirements(item_data)
        atype = cls._determine_atype(item_data)
        socketers = cls._parse_socketers(item_data=item_data)

        item_skills = SkillsFactory.create_skills(item_data)

        cleaned_bgroup = shared_utils.remove_piped_brackets(item_data['properties'][0]['name'])
        category = shared_utils.bgroup_to_category[cleaned_bgroup]

        new_listing = ModifiableListing(
            account_name=listing_data['account']['name'],
            listing_id=api_item_response['id'],
            date_fetched=shared_utils.today_date(),
            minutes_since_listed=minutes_since_listed,
            minutes_since_league_start=minutes_since_league_start,
            currency=listing_data['price']['currency'],
            currency_amount=listing_data['price']['amount'],
            item_name=item_data['name'],
            item_btype=item_data['baseType'] if 'baseType' in item_data else None,
            item_atype=atype,
            item_category=category,
            rarity=item_data['rarity'] if 'rarity' in item_data else None,
            ilvl=item_data['ilvl'] if 'ilvl' in item_data else None,
            identified=item_data['identified'] if 'identified' in item_data else None,
            corrupted='corrupted' in item_data and item_data['corrupted'],
            level_requirement=reqs['level_requirement'],
            str_requirement=reqs['str_requirement'],
            int_requirement=reqs['int_requirement'],
            dex_requirement=reqs['dex_requirement'],
            implicit_mods=[mod for mod in item_mods if mod.mod_class_e == ModClass.IMPLICIT],
            enchant_mods=[mod for mod in item_mods if mod.mod_class_e == ModClass.ENCHANT],
            fractured_mods=[mod for mod in item_mods if mod.mod_class_e == ModClass.FRACTURED],
            explicit_mods=[mod for mod in item_mods if mod.mod_class_e == ModClass.EXPLICIT],
            item_skills=item_skills,
            socketers=socketers,
            open_sockets=len(item_data['sockets']) if 'sockets' in item_data else 0,
            item_properties=properties
        )
        return new_listing
