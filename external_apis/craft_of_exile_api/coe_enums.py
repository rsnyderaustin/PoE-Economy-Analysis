
from enum import Enum


class CoEEndpoint(Enum):
    BASE_TYPES = '/lang/poec_lang.us.json?v=1744834998'
    MODS_AND_WEIGHTS = '/main/poec_data.json?v=1744834989'


class CoEUrl(Enum):
    BASE_URL = 'https://www.craftofexile.com/json/poe2/'


class CoEJsonPath(Enum):
    PATH = ('/Users/austinsnyder/Programming_application_projects/GitHub/'
            'PoE-Economy-Analysis/external_apis/craft_of_exile_api/json_data/poecd_stats.json')

