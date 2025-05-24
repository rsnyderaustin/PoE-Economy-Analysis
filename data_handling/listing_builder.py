import logging

from file_management import FilesManager, DataPath
from instances_and_definitions import ItemMod, SubMod, ItemSkill, ModifiableListing, generate_mod_id
from shared import ATypeClassifier, shared_utils, ModClass, ApiResponseParser
from . import utils
from poecd_api.attribute_finder import PoecdAttributeFinder


class ListingBuilder:

    def __init__(self, poecd_attribute_finder: PoecdAttributeFinder):
        self._mod_resolver = _ModResolver(poecd_attribute_finder)

    def build_listing(self, api_item_response: dict):
        rp = ApiResponseParser(api_item_response)
        minutes_since_listed = utils.determine_minutes_since(
            relevant_date=rp.date_fetched
        )
        minutes_since_league_start = utils.determine_minutes_since(
            relevant_date=utils.league_start_date,
            later_date=rp.date_fetched
        )
        item_mods = self._mod_resolver.resolve_mods(rp)

        listing = ModifiableListing(
            account_name=rp.account_name,
            listing_id=rp.listing_id,
            date_fetched=rp.date_fetched,
            minutes_since_listed=minutes_since_listed,
            minutes_since_league_start=minutes_since_league_start,
            currency=rp.price.currency,
            currency_amount=rp.price.amount,
            item_name=rp.item_name,
            item_btype=rp.item_btype,
            item_atype=ATypeClassifier.classify(rp=rp),
            item_category=rp.item_category,
            rarity=rp.item_rarity,
            ilvl=rp.item_ilvl,
            identified=rp.is_identified,
            corrupted=rp.is_corrupted,
            str_requirement=rp.strength_requirement,
            int_requirement=rp.intelligence_requirement,
            dex_requirement=rp.dexterity_requirement,
            implicit_mods=[mod for mod in item_mods if mod.mod_class_e == ModClass.IMPLICIT],
            enchant_mods=[mod for mod in item_mods if mod.mod_class_e == ModClass.ENCHANT],
            fractured_mods=[mod for mod in item_mods if mod.mod_class_e == ModClass.FRACTURED],
            explicit_mods=[mod for mod in item_mods if mod.mod_class_e == ModClass.EXPLICIT],
            item_skills=_SkillsFactory.create_skills(rp)
        )

        return listing


class _ModResolver:

    def __init__(self, poecd_attribute_finder: PoecdAttributeFinder):
        self.poecd_attribute_finder = poecd_attribute_finder

        files_manager = FilesManager()
        self.file_item_mods = files_manager.file_data[DataPath.MODS] or dict()

    @staticmethod
    def _build_sub_mod(mod_id: str, mod_id_to_text: dict, magnitudes: list[dict]) -> SubMod:
        mod_text = mod_id_to_text[mod_id]
        sanitized_text = shared_utils.sanitize_mod_text(mod_text)
        actual_values = shared_utils.parse_values_from_text(mod_text)

        value_ranges = [
            (
                utils.convert_string_into_number(m['min']) if 'min' in m else None,
                utils.convert_string_into_number(m['max']) if 'max' in m else None
            )
            for m in magnitudes
        ]

        # This is just a temporary error check
        if len(value_ranges) != len(actual_values):
            raise ValueError(f"Item has a different number of ranges and actual values:"
                             f"\n\tRanges: {value_ranges}"
                             f"\n\tActual values: {actual_values}")

        return SubMod(
            mod_id=mod_id,
            sanitized_mod_text=sanitized_text,
            actual_values=actual_values,
            values_ranges=value_ranges
        )

    @classmethod
    def _create_sub_mods(cls, mod_id_to_text: dict, mod_magnitudes: list) -> list[SubMod]:
        # Sub-mods within a hybrid mod that share a magnitude represent a range of values
        mod_id_to_mags = dict()
        for magnitude in mod_magnitudes:
            if magnitude['hash'] not in mod_id_to_mags:
                mod_id_to_mags[magnitude['hash']] = list()

            mod_id_to_mags[magnitude['hash']].append(magnitude)

        sub_mods = []
        for mod_id, magnitudes in mod_id_to_mags.items():
            sub_mod = cls._build_sub_mod(mod_id, mod_id_to_text, magnitudes)
            sub_mods.append(sub_mod)

        return sub_mods

    def _create_item_mod(self, mod_data: dict, mod_id_to_text: dict, mod_class: ModClass, atype: str):
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

    def resolve_mods(self, rp: ApiResponseParser) -> list[ItemMod]:
        """
        Attempts to pull each mod in the item's data from file. Otherwise, it manages the mod's creation and caching
        :return: All mods from the item data
        """
        mods = []

        atype = ATypeClassifier.classify(rp)

        mod_datas = [
            (mod_class_e, mod_data)
            for mod_class_e in rp.mod_classes
            for mod_data in rp.fetch_mods_data(mod_class_e)
        ]
        for mod_class_e, mod_data in mod_datas:
            mod_ids = set(magnitude['hash'] for magnitude in mod_data['magnitudes'])
            affix_type = utils.determine_mod_affix_type(mod_data)
            mod_id = generate_mod_id(atype=atype, mod_ids=mod_ids, affix_type=affix_type)

            if mod_id in self.file_item_mods:
                mods.append(self.file_item_mods[mod_id])
                continue

            logging.info(f"Could not find mod with ID {mod_id}. Creating and caching.")
            new_mod = self._create_item_mod(mod_data=mod_data,
                                            mod_id_to_text=rp.fetch_mod_id_to_mod_text(mod_class_e),
                                            mod_class=mod_class_e,
                                            atype=atype)
            self.file_item_mods[new_mod.mod_id] = new_mod  # Add the new mod to our mod JSON file
            mods.append(new_mod)

        return mods


class _SkillsFactory:

    @staticmethod
    def create_skills(rp: ApiResponseParser) -> list[ItemSkill]:
        if not rp.skills_data:
            return []

        skills = []
        for skill_data in rp.skills_data:
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
