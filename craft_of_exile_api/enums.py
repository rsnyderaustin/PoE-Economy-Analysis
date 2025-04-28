
from enum import Enum


class Endpoint(Enum):
    BASE_TYPES = '/lang/poec_lang.us.json?v=1744834998'
    MODS_AND_WEIGHTS = '/main/poec_data.json?v=1744834989'


class Url(Enum):
    BASE_URL = 'https://www.craftofexile.com/json/poe2/'