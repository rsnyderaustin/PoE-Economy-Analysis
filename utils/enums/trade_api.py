
from enum import Enum


class TypeFilter(Enum):
    ITEM_CATEGORY = 'category'
    ILVL = 'ilvl'


class StatFilterType(Enum):
    AND = 'and'
    WEIGHTED = 'weight'
    WEIGHTED_V2 = 'weight2'
    IF_PRESENT = 'if'
    COUNT = 'count'


class MetaSearchType(Enum):
    EQUIPMENT = 'equipment_filters'
    TRADE = 'trade_filters'
    REQUIREMENT = 'req_filters'
    TYPE = 'type_filters'
    MISC = 'misc_filters'


class MiscSearchParameter(Enum):
    FILTERS = 'filters'
    STATS = 'stats'
    STATUS = 'status'
    DISABLED = 'disabled'
    OPTION = 'option'
    PRICE = 'price'
    MIN = 'min'
    MAX = 'max'
    VALUE = 'value'
    ID = 'id'
    WEIGHT = 'weight'
    TYPE = 'type'


class ListedSince(Enum):
    UP_TO_1_HOUR = '1hour'
    UP_TO_3_HOURS = '3hours'
    UP_TO_12_HOURS = '12hours'
    UP_TO_1_DAY = '1day'
    UP_TO_3_DAYS = '3days'
    UP_TO_1_WEEK = '1week'
    UP_TO_2_WEEKS = '2weeks'
    UP_TO_1_MONTH = '1month'
    UP_TO_2_MONTHS = '2months'


class TradeApiConfig(Enum):
    QUERY_WAIT_TIME = 0.5
    API_JSON_DATA_BASE_URL = 'https://www.pathofexile.com/api/trade2/data/'
    JSON_FILE_PATH = '/external_apis/official_api/json_data/'

