import itertools
import uuid
from abc import ABC, abstractmethod
from enum import Enum

from src.market_item_analysis import trade_api
from src.market_item_analysis.core.enums.trade import TradeQueryMetaFilterDefinition, \
    TradeQueryStatsFilterGroupDefinition, TradeSearchType
from src.market_item_analysis.core.types import Range, ListIndex
from src.market_item_analysis.trade_api.query.builder import TradeApiQueryEntry


class TradeApiQueryFilter(ABC):

    def __init__(self):
        self.filter_id = uuid.uuid4()

class TradeApiMetaFilter(ABC, TradeApiQueryFilter):

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

class TradeApiEnumMetaFilter(TradeApiMetaFilter):

    def __init__(self, filter_definition: TradeQueryMetaFilterDefinition, enum_value: Enum):
        super().__init__(filter_definition)
        self.enum_value = enum_value

    @property
    def splittable(self) -> bool:
        return False

    @property
    def query_value(self):
        return self.enum_value.value

class TradeApiRangeMetaFilter(TradeApiMetaFilter):

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

class TradeApiBoolMetaFilter(TradeApiMetaFilter):

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

class TradeApiStatFilter(TradeApiQueryFilter):

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


class TradeApiStatFiltersGroup:

    def __init__(self,
                 filter_group_definition: TradeQueryStatsFilterGroupDefinition,
                 stat_filters: list[TradeApiStatFilter],
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

class TradeApiQueryPlan:

    def __init__(self,
                 meta_filters: list[TradeApiMetaFilter],
                 stat_filters_groups: list[TradeApiStatFiltersGroup] | None = None):
        self._meta_filters = {meta_filter.filter_id: meta_filter for meta_filter in meta_filters}
        self.stat_filters_groups = stat_filters_groups or []

    @property
    def meta_filters(self) -> list[TradeApiMetaFilter]:
        return list(self._meta_filters.values())

    def clone_with_new_filter(self, original_filter: TradeApiQueryFilter, new_filter: TradeApiQueryFilter) -> "TradeApiQueryPlan":
        if isinstance(original_filter, )
        new_filters = [
            new_filter if f is original_filter else f
            for f in self.meta_filters
        ]
        return TradeApiQueryPlan(meta_filters=new_filters,
                                 stat_filters_groups=self.stat_filters_groups)

        self._meta_filters[new_filter.filter_id] = new_filter


@dataclass
class TradeApiQueryEntry:
    keys_path: list[DictKey | ListIndex]
    value: dict | list

class TradeApiQuery:

    def __init__(self):
        self._d = {
            'query': {
                'status': {
                    'option': 'securable'
                }
            }
        }

    def insert_value(self, entry: TradeApiQueryEntry):
        current = self._d

        for i, key in enumerate(entry.keys_path):
            is_last = (i == len(entry.keys_path) - 1)

            if isinstance(key, DictKey):
                if is_last:
                    current[key.key] = entry.value
                else:
                    # Initialize dict if missing
                    if key.key not in current or not isinstance(current[key.key], dict):
                        current[key.key] = {}
                    current = current[key.key]

            elif isinstance(key, ListIndex):
                # Ensure the list is long enough
                while len(current) <= key.index:
                    current.append({})

                if is_last:
                    current[key.index] = entry.value
                else:
                    current = current[key.index]
            else:
                raise TypeError(f"Unsupported key type {type(key)}")

