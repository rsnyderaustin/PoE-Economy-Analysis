from dataclasses import dataclass
from typing import Any

from src.market_item_analysis.trade_api.query import QueryPlan
from src.market_item_analysis.core.types import ListIndex, DictKey

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

class TradeApiQueryBuilder:

    @classmethod
    def build(cls, query_plan: QueryPlan) -> TradeApiQuery:
        query = TradeApiQuery()

        for meta_filter in query_plan.meta_filters:
            query.insert_value(entry=meta_filter.query_entry)

        for stat_filter_group in query_plan.stat_filters_groups:
            query.insert_value(entry=stat_filter_group.query_entry)

        return query


