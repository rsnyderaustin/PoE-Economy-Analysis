from .query_filters import MetaFilter, StatsFiltersGroup, StatFilter
from .trade_api_utils import (StatSearchType)


class TradeQueryConstructor:

    def __init__(self):
        self.query = {
            'query': {
                'status': {'option': 'online'}
            }
        }

    def create_trade_query(self,
                           meta_mod_filters: list[MetaFilter] = None,
                           stats_filter_groups: list[StatsFiltersGroup] = None):
        if meta_mod_filters:
            self._handle_meta_query(meta_mod_filters=meta_mod_filters)

        if stats_filter_groups:
            self._handle_stats_query(stats_filters_groups=stats_filter_groups)
        else:
            self.query['query']['stats'] = [
                {
                    'filters': [],
                    'type': 'and'
                }
            ]

        return self.query

    def _handle_meta_query(self, meta_mod_filters: list[MetaFilter]):
        self.query['query']['filters'] = dict()
        meta_query = self.query['query']['filters']
        for meta_filter in meta_mod_filters:
            if meta_filter.meta_search_type not in meta_query:
                meta_query[meta_filter.meta_search_type] = dict()
                meta_query[meta_filter.meta_search_type]['filters'] = dict()

            filter_group_dict = meta_query[meta_filter.meta_search_type]['filters']

            filter_group_dict[meta_filter.filter_type] = dict()
            meta_mod_dict = filter_group_dict[meta_filter.filter_type]

            meta_mod_dict['option'] = meta_filter.filter_value
            if meta_filter.currency_amount:
                if meta_filter.currency_amount[0] is not None:
                    meta_mod_dict['min'] = meta_filter.currency_amount[0]
                if meta_filter.currency_amount[1]:
                    meta_mod_dict['max'] = meta_filter.currency_amount[1]

    def _handle_stats_query(self, stats_filters_groups: list[StatsFiltersGroup]):
        self.query['stats'] = dict()
        stats_dict = self.query['stats']

        if not stats_filters_groups:
            stats_dict[0] = {
                'filters': [],
                'type': StatSearchType.AND.value
            }

            return

        # Each StatsFiltersGroup is a group with a type such as AND, IF, WEIGHTED_SUMV2, etc that possibly
        # holds individual mod filters
        for i, stats_filters_group in enumerate(stats_filters_groups):
            if stats_filters_group.filter_type not in StatSearchType:
                raise ValueError(f"FilterType {stats_filters_group.filter_type} not one of acceptable "
                                 f"FilterTypes {StatSearchType}.")

            stats_dict['type'] = stats_filters_group.filter_type.value

            # Take care of the overall stats group value range (for weightedV2, count, etc)
            if stats_filters_group.value_range:
                stats_dict['value'] = {

                }
                value_dict = stats_dict['value']
                if stats_filters_group.value_range[0]:
                    value_dict['min'] = stats_filters_group.value_range[0]
                if stats_filters_group.value_range[1]:
                    value_dict['max'] = stats_filters_group.value_range[1]

            """
            Can't really tell yet when this is needed vs not
            stats_dict[i] = {
                MiscSearchParameter.DISABLED.value: False
            }"""

            # Take care of inserting individual mods within the stats group
            if stats_filters_group.mod_filters:
                stats_dict['filters'] = dict()
                mod_filters_dict = stats_dict['filters']

                for i, mod_filter in enumerate(stats_filters_group.mod_filters):
                    mod_filters_dict[i] = {
                        'id': mod_filter.mod_enum.value
                    }

                    if mod_filter.values_range or mod_filter.weight:
                        mod_filters_dict[i]['value'] = dict()
                        mod_values_dict = mod_filters_dict[i]['value']

                        if mod_filter.values_range:
                            _handle_min_max(relevant_dict=mod_values_dict,
                                            query_filter=mod_filter)
                        if mod_filter.weight:
                            mod_values_dict['weight'] = mod_filter.weight



