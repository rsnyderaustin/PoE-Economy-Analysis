
from enum import Enum


class TypeFilter(Enum):
    ITEM_CATEGORY = 'category'
    ILVL = 'ilvl'


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
