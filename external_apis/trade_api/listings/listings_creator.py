
from .item_listing import ItemListing
from .mods_creator import ModsCreator
from .skills_creator import SkillsCreator
from utils.enums import ModClass


class ListingsCreator:

    @classmethod
    def create_listings(cls, api_items_responses: list[dict]):
        new_listings = []
        for re in api_items_responses:
            li = re['listing']
            it = re['item']
            level_requirement = None
            str_requirement = 0
            int_requirement = 0
            dex_requirement = 0
            for req_dict in it['requirements']:
                if req_dict['name'] == 'Level':
                    level_requirement = int(req_dict['values'][0][0])
                if 'Str' in req_dict['name']:
                    str_requirement = int(req_dict['values'][0][0])
                if 'Int' in req_dict['name']:
                    int_requirement = int(req_dict['values'][0][0])
                if 'Dex' in req_dict['name']:
                    dex_requirement = int(req_dict['values'][0][0])

            implicit_mods = ModsCreator.create_mods(it, ModClass.IMPLICIT) if 'implicitMods' in it else None
            explicit_mods = ModsCreator.create_mods(it, ModClass.EXPLICIT) if 'explicitMods' in it else None
            enchant_mods = ModsCreator.create_mods(it, ModClass.ENCHANT) if 'enchantMods' in it else None
            fractured_mods = ModsCreator.create_mods(it, ModClass.FRACTURED) if 'fracturedMods' in it else None
            rune_mods = ModsCreator.create_mods(it, ModClass.RUNE) if 'runeMods' in it else None
            skills = SkillsCreator.create_skills(it['grantedSkills']) if 'grantedSkills' in it else None

            new_listing = ItemListing(
                listing_id=re['id'],
                date_fetched=li['indexed'],
                price_currency=li['price']['currency'],
                price_amount=li['price']['amount'],
                item_name=it['name'],
                raw_item_btype=it['baseType'],
                item_bgroup=it['properties'][0]['name'],
                rarity=it['rarity'],
                ilvl=it['ilvl'],
                identified=it['identified'],
                corrupted='corrupted' in it,
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
