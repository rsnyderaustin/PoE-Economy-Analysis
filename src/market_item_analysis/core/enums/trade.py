from enum import Enum, auto

from src.market_item_analysis.core.types import Range, ListIndex, DictKey
from src.market_item_analysis.trade_api.query.builder import TradeApiQueryEntry


class TradeSearchCategory(Enum):
    TYPE = 'type_filters'
    EQUIPMENT = 'equipment_filters'
    REQUIREMENT = 'req_filters'
    MISC = 'misc_filters'
    TRADE = 'trade_filters'


class TradeSearchType(Enum):
    RANGE = auto()
    DROP_DOWN = auto()
    USER_INPUT = auto()


class TradeQueryStatsFilterGroupDefinition(Enum):
    AND = (None, 'and')
    WEIGHTED = (TradeSearchType.RANGE, 'weight')
    WEIGHTED_V2 = (TradeSearchType.RANGE, 'weight2')
    IF_PRESENT = (None, 'if')
    COUNT = (TradeSearchType.RANGE, 'count')

    def __init__(self, search_type: TradeSearchType | None, query_key: str):
        self.search_type = search_type
        self.query_key = query_key

    def query_entry(self,
                    filter_group_index: ListIndex,
                    range_value: Range | None) -> TradeApiQueryEntry:
        query_path = ['query', 'stats', filter_group_index]
        query_value = self._query_value(value=range_value)

        return TradeApiQueryEntry(
            keys_path=query_path,
            value=query_value
        )

    def _query_value(self, value: Range | None) -> dict:
        base_d = {
            'type': self.query_key
        }
        if self.search_type == TradeSearchType.RANGE:
            if value is not None:
                base_d['value'] = value.query_value
        else:
            raise TypeError(f"Unsupported TradeSearchType: {self.search_type}")

        return base_d


class TradeQueryMetaFilterDefinition(Enum):
    ITEM_CATEGORY = (TradeSearchCategory.TYPE, TradeSearchType.DROP_DOWN, 'category')
    ITEM_RARITY = (TradeSearchCategory.TYPE, TradeSearchType.DROP_DOWN, 'rarity')
    ITEM_LEVEL = (TradeSearchCategory.TYPE, TradeSearchType.RANGE, 'ilvl')
    ITEM_QUALITY = (TradeSearchCategory.TYPE, TradeSearchType.RANGE, 'quality')
    BUYOUT_TYPE = (TradeSearchCategory.TYPE, TradeSearchType.DROP_DOWN, 'buyout_type')

    IDENTIFIED = (TradeSearchCategory.MISC, TradeSearchType.DROP_DOWN, 'identified')
    CORRUPTED = (TradeSearchCategory.MISC, TradeSearchType.DROP_DOWN, 'corrupted')
    MIRRORED = (TradeSearchCategory.MISC, TradeSearchType.DROP_DOWN, 'mirrored')

    LEVEL_REQUIRED = (TradeSearchCategory.REQUIREMENT, TradeSearchType.RANGE, 'lvl')
    STRENGTH_REQUIRED = (TradeSearchCategory.REQUIREMENT, TradeSearchType.RANGE, 'str')
    DEXTERITY_REQUIRED = (TradeSearchCategory.REQUIREMENT, TradeSearchType.RANGE, 'dex')
    INTELLIGENCE_REQUIRED = (TradeSearchCategory.REQUIREMENT, TradeSearchType.RANGE, 'int')

    ARMOUR = (TradeSearchCategory.EQUIPMENT, TradeSearchType.RANGE, 'ar')
    EVASION = (TradeSearchCategory.EQUIPMENT, TradeSearchType.RANGE, 'ev')
    ENERGY_SHIELD = (TradeSearchCategory.EQUIPMENT, TradeSearchType.RANGE, 'es')
    BLOCK = (TradeSearchCategory.EQUIPMENT, TradeSearchType.RANGE, 'block')
    SPIRIT = (TradeSearchCategory.EQUIPMENT, TradeSearchType.RANGE, 'spirit')
    RUNE_SOCKETS = (TradeSearchCategory.EQUIPMENT, TradeSearchType.RANGE, 'rune_sockets')

    WEAPON_DAMAGE = (TradeSearchCategory.EQUIPMENT, TradeSearchType.RANGE, 'damage')
    ATTACKS_PER_SECOND = (TradeSearchCategory.EQUIPMENT, TradeSearchType.RANGE, 'aps')
    CRIT_CHANCE = (TradeSearchCategory.EQUIPMENT, TradeSearchType.RANGE, 'crit')
    DPS = (TradeSearchCategory.EQUIPMENT, TradeSearchType.RANGE, 'dps')
    PHYSICAL_DPS = (TradeSearchCategory.EQUIPMENT, TradeSearchType.RANGE, 'pdps')
    ELEMENTAL_DPS = (TradeSearchCategory.EQUIPMENT, TradeSearchType.RANGE, 'edps')

    LISTED_SINCE = (TradeSearchCategory.TRADE, TradeSearchType.DROP_DOWN, 'indexed')
    LISTING_PRICE = (TradeSearchCategory.TRADE, TradeSearchType.RANGE, 'price')
    LISTING_CURRENCY = (TradeSearchCategory.TRADE, TradeSearchType.DROP_DOWN, 'price')

    def __init__(self,
                 search_category: TradeSearchCategory,
                 search_type: TradeSearchType,
                 query_key: str):
        self.search_category = search_category
        self.search_type = search_type
        self.query_key = query_key

    def query_entry(self, trade_search_type: TradeSearchType) -> TradeApiQueryEntry:
        query_path = [DictKey('query'), DictKey('filters'), DictKey(self.search_category.value), DictKey(self.query_key)]
        query_value = self._format_query_value(value=trade_search_type)

        return TradeApiQueryEntry(
            keys_path=query_path,
            value=query_value
        )

    def _format_query_value(self, value) -> dict:
        if self.search_type == TradeSearchType.RANGE:
            return {
                'min': value[0],
                'max': value[1]
            }
        elif self.search_type == TradeSearchType.DROP_DOWN:
            value = value.value if isinstance(value, Enum) else value
            return {
                'option': value
            }
        else:
            raise TypeError(f"Unsupported search type: {self.search_type}")

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


class Currency(Enum):
    TRANSMUTATION_SHARD = "transmutation-shard"
    CHANCE_SHARD = "chance-shard"
    REGAL_SHARD = "regal-shard"
    ARTIFICERS_SHARD = "artificers-shard"
    SCROLL_OF_WISDOM = "wisdom"
    ORB_OF_TRANSMUTATION = "transmute"
    ORB_OF_AUGMENTATION = "aug"
    ORB_OF_CHANCE = "chance"
    ORB_OF_ALCHEMY = "alch"
    CHAOS_ORB = "chaos"
    VAAL_ORB = "vaal"
    REGAL_ORB = "regal"
    EXALTED_ORB = "exalted"
    DIVINE_ORB = "divine"
    ORB_OF_ANNULMENT = "annul"
    ARTIFICERS_ORB = "artificers"
    FRACTURING_ORB = "fracturing-orb"
    MIRROR_OF_KALANDRA = "mirror"
    ARMOURERS_SCRAP = "scrap"
    BLACKSMITHS_WHETSTONE = "whetstone"
    ARCANISTS_ETCHER = "etcher"
    GLASSBLOWERS_BAUBLE = "bauble"
    GEMCUTTERS_PRISM = "gcp"
