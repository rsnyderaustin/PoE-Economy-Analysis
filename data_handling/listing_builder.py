import logging
import pprint

from file_management import FilesManager, DataPath
from instances_and_definitions import ItemMod, SubMod, ItemSkill, ModifiableListing, generate_mod_id
from poecd_api import GlobalPoecdAtypeModsManager
from shared import ATypeClassifier, shared_utils, ModClass, ApiResponseParser
from . import utils
from poecd_api.mods_management import GlobalPoecdAtypeModsManager
from .mod_matching import ModMatcher


class ListingBuilder:

    def __init__(self, global_atypes_manager: GlobalPoecdAtypeModsManager):
        self._mod_resolver = _ModResolver(global_atypes_manager)

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
            implicit_mods=[mod for mod in item_mods if mod.mod_class_e == ModClass.IMPLICIT],
            enchant_mods=[mod for mod in item_mods if mod.mod_class_e == ModClass.ENCHANT],
            fractured_mods=[mod for mod in item_mods if mod.mod_class_e == ModClass.FRACTURED],
            explicit_mods=[mod for mod in item_mods if mod.mod_class_e == ModClass.EXPLICIT],
            item_skills=_SkillsFactory.create_skills(rp)
        )

        return listing


class _ModResolver:

    def __init__(self, global_poecd_mods_manager: GlobalPoecdAtypeModsManager):
        self._global_poecd_mods_manager = global_poecd_mods_manager
        self.mod_matcher = ModMatcher(global_poecd_mods_manager)

        files_manager = FilesManager()
        self.file_item_mods = files_manager.file_data[DataPath.MODS] or dict()

        self.current_rp = None

    def _create_sub_mods(self, current_mod: ItemMod, mod_magnitudes: list) -> list[SubMod]:
        # Sub-mods within a hybrid mod that share a magnitude represent a range of values
        mod_id_to_mags = dict()
        for magnitude in mod_magnitudes:
            if magnitude['hash'] not in mod_id_to_mags:
                mod_id_to_mags[magnitude['hash']] = list()

            mod_id_to_mags[magnitude['hash']].append(magnitude)

        mod_id_to_text = self.current_rp.fetch_mod_id_to_text(current_mod.mod_class_e)
        sub_mods = []
        for mod_id, magnitudes in mod_id_to_mags.items():
            mod_text = mod_id_to_text[mod_id]

            value_ranges = [
                (
                    utils.convert_string_into_number(m['min']) if 'min' in m else None,
                    utils.convert_string_into_number(m['max']) if 'max' in m else None
                )
                for m in magnitudes
            ]
            new_sub_mod = SubMod(
                mod_id=mod_id,
                sanitized_mod_text=shared_utils.sanitize_mod_text(mod_text),
                actual_values=shared_utils.extract_values_from_text(mod_text),
                values_ranges=value_ranges
            )
            sub_mods.append(new_sub_mod)

        return sub_mods

    def _create_item_mod(self, mod_data: dict, mod_class: ModClass):
        new_mod = ItemMod(
            atype=self.current_atype,
            mod_class_e=mod_class,
            mod_name=mod_data['name'],
            affix_type_e=utils.determine_mod_affix_type(mod_data),
            mod_tier=utils.determine_mod_tier(mod_data),
            mod_ilvl=int(mod_data['level'])
        )
        magnitudes = mod_data['magnitudes']

        sub_mods = self._create_sub_mods(
            current_mod=new_mod,
            mod_magnitudes=magnitudes
        )

        new_mod.insert_sub_mods(sub_mods)

        matched_poecd_mod_id = self.mod_matcher.match_mod(new_mod)

        if not matched_poecd_mod_id:
            raise RuntimeError(f"Was not able to match item mod:\n{pprint.pprint(new_mod)}")

        poecd_mod = self._global_poecd_mods_manager.fetch_mod(atype=new_mod.atype,
                                                              mod_id=matched_poecd_mod_id)
        new_mod.weighting = poecd_mod.fetch_weighting(ilvl=int(mod_data['level']))
        new_mod.mod_types = poecd_mod.mod_types

        return new_mod

    def resolve_mods(self, rp: ApiResponseParser) -> list[ItemMod]:
        """
        Attempts to pull each mod in the item's data from file. Otherwise, it manages the mod's creation and caching
        :return: All mods from the item data
        """
        self.current_rp = rp
        self.current_atype = ATypeClassifier.classify(rp)

        mods = []

        mod_datas = [
            (mod_class_e, mod_data)
            for mod_class_e in rp.mod_classes
            for mod_data in rp.fetch_mods_data(mod_class_e)
        ]
        for mod_class_e, mod_data in mod_datas:
            mod_ids = set(magnitude['hash'] for magnitude in mod_data['magnitudes'])
            affix_type = utils.determine_mod_affix_type(mod_data)
            mod_id = generate_mod_id(atype=self.current_atype, mod_ids=mod_ids, affix_type=affix_type)

            if mod_id in self.file_item_mods:
                mods.append(self.file_item_mods[mod_id])
                continue

            logging.info(f"Could not find mod with ID {mod_id}. Creating and caching.")
            new_mod = self._create_item_mod(mod_data=mod_data,
                                            mod_class=mod_class_e)
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
