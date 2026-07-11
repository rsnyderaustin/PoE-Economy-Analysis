import itertools
import uuid
from abc import ABC, abstractmethod
from enum import Enum

from src.market_item_analysis import trade_api
from src.market_item_analysis.core.enums.trade import TradeQueryMetaFilterDefinition, \
    TradeQueryStatsFilterGroupDefinition, TradeSearchType
from src.market_item_analysis.core.types import Range, ListIndex
from src.market_item_analysis.trade_api.query.construction import TradeApiQueryEntry


class TradeApiQueryFilter(ABC):

    def __init__(self):
        self.filter_id = uuid.uuid4()

class MetaFilter(ABC, TradeApiQueryFilter):

    def __init__(self,
                 filter_definition: TradeQueryMetaFilterDefinition):
        super().__init__()
        self.filter_definition = filter_definition

    @abstractmethod
    @property
    def splittable(self) -> bool:
        pass

    @property
    def query_entry(self, trade_search_type: TradeSearchType) -> TradeApiQueryEntry:
        filter_definition_query_entry = self.filter_definition.query_entry(trade_search_type=trade_search_type)
        return TradeApiQueryEntry(
            keys_path=filter_definition_query_entry.keys_path,
            value=self.query_value
        )

    @abstractmethod
    @property
    def query_value(self):
        pass

class EnumMetaFilter(MetaFilter):

    def __init__(self, filter_definition: TradeQueryMetaFilterDefinition, enum_value: Enum):
        super().__init__(filter_definition)
        self.enum_value = enum_value

    @property
    def splittable(self) -> bool:
        return False

    @property
    def query_value(self):
        return self.enum_value.value

class RangeMetaFilter(MetaFilter):

    def __init__(self, filter_definition: TradeQueryMetaFilterDefinition, values_range: Range):
        super().__init__(filter_definition)

        if len(values_range) != 2:
            raise ValueError(f"Expected two values, got {values_range}")

        self.values_range = values_range

    @property
    def splittable(self) -> bool:
        return not self.values_range.is_point

    @property
    def query_value(self):
        return self.values_range.query_value

class BoolMetaFilter(MetaFilter):

    def __init__(self, filter_definition: TradeQueryMetaFilterDefinition, bool_value: bool):
        super().__init__(filter_definition)
        self.bool_value = bool_value

    @property
    def splittable(self) -> bool:
        return False

    @property
    def query_value(self):
        bool_d = {
            True: 'true',
            False: 'false'
        }
        return bool_d[self.bool_value]

class StatFilter(TradeApiQueryFilter):

    def __init__(self,
                 mod_id: str,
                 values_range: Range | None = None,
                 weight: float | None = None):
        super().__init__()
        self.mod_id = mod_id
        self.values_range = values_range
        self.weight = weight

    @property
    def query_value(self) -> dict:
        base_d = {
            'disabled': False,
            'id': self.mod_id
        }

        if self.values_range is not None or self.weight is not None:
            if self.values_range is not None:
                value_d = self.values_range.query_value
            else:
                value_d = dict()

            if self.weight is not None:
                value_d['weight'] = self.weight

            base_d['value'] = value_d

        return base_d


class StatFiltersGroup:

    def __init__(self,
                 filter_group_definition: TradeQueryStatsFilterGroupDefinition,
                 stat_filters: list[StatFilter],
                 value_range: Range | None = None):
        self.filter_group_definition = filter_group_definition
        self.value_range = value_range

        self.stat_filters = stat_filters

    def query_entry(self, filter_group_index: ListIndex) -> TradeApiQueryEntry:
        filter_group_entry = self.filter_group_definition.query_entry(filter_group_index=filter_group_index)

        filter_group_value = filter_group_entry.value

        stats_list = filter_group_value['stats'] = []
        for i, stat_filter in enumerate(self.stat_filters):
            query_value = stat_filter.query_value
            stats_list.append(query_value)

        return TradeApiQueryEntry(
            keys_path=filter_group_entry.keys_path,
            value=filter_group_value
        )

class QueryPlan:

    def __init__(self,
                 meta_filters: list[MetaFilter],
                 stat_filters_groups: list[StatFiltersGroup] | None = None):
        self._meta_filters = {meta_filter.filter_id: meta_filter for meta_filter in meta_filters}
        self.stat_filters_groups = stat_filters_groups or []

    @property
    def meta_filters(self) -> list[MetaFilter]:
        return list(self._meta_filters.values())

    def clone_with_new_filter(self, original_filter: TradeApiQueryFilter, new_filter: TradeApiQueryFilter) -> "QueryPlan":
        if isinstance(original_filter, )
        new_filters = [
            new_filter if f is original_filter else f
            for f in self.meta_filters
        ]
        return QueryPlan(meta_filters=new_filters,
                         stat_filters_groups=self.stat_filters_groups)

        self._meta_filters[new_filter.filter_id] = new_filter

class QueryPresets:

    @classmethod
    def training_data(cls) -> list[QueryPlan]:
        item_categories = EquipmentCategoryGroups.fetch_martial_weapon_categories(which=WhichCategoryType.TRADE)
        currencies = [trade_enums.Currency.DIVINE_ORB]

        currency_amounts = [(1, 1)]
        for i in range(1, 8):
            first_num = currency_amounts[i - 1][1] + 1
            second_num = first_num + i * 2
            currency_amounts.append((first_num, second_num))

        queries = []
        for item_category, currency, currency_amount in itertools.product(item_categories, currencies, currency_amounts):
            ilvl_filter = trade_api.MetaFilter(
                filter_type_enum=trade_enums.TypeFilter.ITEM_LEVEL,
                filter_value=(71, 100)
            )

            category_filter = trade_api.MetaFilter(
                filter_type_enum=trade_enums.TypeFilter.ITEM_CATEGORY,
                filter_value=item_category
            )

            days_since_listed_filter = trade_api.MetaFilter(
                filter_type_enum=trade_enums.TradeFilter.LISTED,
                filter_value=trade_enums.ListedSince.UP_TO_1_HOUR
            )

            price_filter = trade_api.MetaFilter(
                filter_type_enum=trade_enums.TradeFilter.PRICE,
                filter_value=currency,
                currency_amount=currency_amount
            )

            rarity_filter = trade_api.MetaFilter(
                filter_type_enum=trade_enums.TypeFilter.ITEM_RARITY,
                filter_value=trade_enums.Rarity.RARE
            )

            meta_mod_filters = [ilvl_filter, category_filter, price_filter, rarity_filter, days_since_listed_filter]
            query = trade_api.Query(meta_filters=meta_mod_filters)
            queries.append(query)

        return queries
