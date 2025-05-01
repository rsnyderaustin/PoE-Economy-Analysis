
import logging

from external_apis.trade_api.things.item_listing import ItemListing
from .mods_creator import ModsCreator
from .skills_creator import SkillsCreator
from utils.enums import ModClass, ItemCategory
from ..raw_btype_to_btye import RawCategoryToCategory


class ListingsCreator:

    _invalid_btypes = {
        ItemCategory.RUNE.value
    }

    _unmodifiable_btypes = {
        ItemCategory.GEM.value
    }

    @classmethod
    def _clean_api_item_responses(cls, api_item_responses: list[dict]):
        """
        Right now this is just used to clear empty implicits from spears granting skill Spear Throw.
        """
        for response in api_item_responses:
            item_data = response['item']
            if 'extended' in item_data and item_data['extended'] and 'implicit' in item_data['extended']['mods']:
                implicit_mod_dicts = item_data['extended']['mods']['implicit']

                implicit_mod_dicts[:] = [
                    implicit_mod_dict
                    for implicit_mod_dict in implicit_mod_dicts
                    if (implicit_mod_dict['magnitudes'] or implicit_mod_dict['name'] or implicit_mod_dict['tier'])
                ]

    @classmethod
    def create_listings(cls, api_items_responses: list[dict]):
        cls._clean_api_item_responses(api_items_responses)

        new_listings = []
        for re in api_items_responses:
            li = re['listing']
            it = re['item']

            if it['baseType'] in cls._invalid_btypes:
                logging.error(f"Received API item response for btype {it['baseType']}. Skipping.")
                continue

            level_requirement = 0
            str_requirement = 0
            int_requirement = 0
            dex_requirement = 0

            if 'requirements' in it:
                for req_dict in it['requirements']:
                    if req_dict['name'] == 'Level':
                        level_requirement = int(req_dict['values'][0][0])
                    if 'Str' in req_dict['name']:
                        str_requirement = int(req_dict['values'][0][0])
                    if 'Int' in req_dict['name']:
                        int_requirement = int(req_dict['values'][0][0])
                    if 'Dex' in req_dict['name']:
                        dex_requirement = int(req_dict['values'][0][0])

            if 'properties' in it and 'name' in it['properties'][0]:
                raw_category = it['properties'][0]['name']
                category = RawCategoryToCategory.convert(
                    raw_category=raw_category,
                    str_requirement=str_requirement,
                    int_requirement=int_requirement,
                    dex_requirement=dex_requirement
                )
            else:
                category = it['baseType'] if 'baseType' in it else None

            implicit_mods = []
            explicit_mods = []
            enchant_mods = []
            fractured_mods = []
            rune_mods = []
            skills = []
            if it['baseType'] not in cls._unmodifiable_btypes:
                implicit_mods = ModsCreator.create_mods(it, ModClass.IMPLICIT) if 'implicitMods' in it else []
                explicit_mods = ModsCreator.create_mods(it, ModClass.EXPLICIT) if 'explicitMods' in it else []
                enchant_mods = ModsCreator.create_mods(it, ModClass.ENCHANT) if 'enchantMods' in it else []
                fractured_mods = ModsCreator.create_mods(it, ModClass.FRACTURED) if 'fracturedMods' in it else []
                rune_mods = ModsCreator.create_mods(it, ModClass.RUNE) if 'runeMods' in it else []
                skills = SkillsCreator.create_skills(it['grantedSkills']) if 'grantedSkills' in it else []

            new_listing = ItemListing(
                listing_id=re['id'],
                date_fetched=li['indexed'],
                price_currency=li['price']['currency'],
                price_amount=li['price']['amount'],
                item_name=it['name'],
                item_btype=it['baseType'] if 'baseType' in it else None,
                item_category=category,
                item_bgroup=it['properties'][0]['name'],
                rarity=it['rarity'] if 'rarity' in it else None,
                ilvl=it['ilvl'] if 'ilvl' in it else None,
                identified=it['identified'] if 'identified' in it else None,
                corrupted='corrupted' in it and it['corrupted'],
                level_requirement=level_requirement,
                str_requirement=str_requirement,
                int_requirement=int_requirement,
                dex_requirement=dex_requirement,
                implicit_mods=implicit_mods,
                enchant_mods=enchant_mods,
                rune_mods=rune_mods,
                fractured_mods=fractured_mods,
                explicit_mods=explicit_mods,
                item_skills=skills
            )
            new_listings.append(new_listing)

        return new_listings
