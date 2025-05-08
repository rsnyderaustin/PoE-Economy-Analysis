from .query import MetaFilter, StatsFiltersGroup, Query
from shared.trade_item_enums import (StatSearchType)
import external_apis


def create_trade_query(query: Query):
    query_dict = {
        'query': {
            'status': {'option': 'online'}
        }
    }
    if query.meta_filters:
        query_dict['query']['filters'] = dict()
        _handle_meta_query(meta_dict=query_dict['query']['filters'],
                           meta_filters=query.meta_filters)

    if query.stats_filters_groups:
        query_dict['stats'] = dict()
        _handle_stats_query(stats_dict=query_dict['stats'],
                            stats_filters_groups=query.stats_filters_groups)
    else:
        query_dict['query']['stats'] = [
            {
                'filters': [],
                'type': 'and'
            }
        ]
    return query_dict

def _handle_meta_query(meta_dict: dict, meta_filters: list[MetaFilter]):
    for meta_filter in meta_filters:
        if meta_filter.meta_search_type not in meta_dict:
            meta_dict[meta_filter.meta_search_type] = dict()
            meta_dict[meta_filter.meta_search_type]['filters'] = dict()

        filter_group_dict = meta_dict[meta_filter.meta_search_type]['filters']

        filter_group_dict[meta_filter.filter_type] = dict()
        meta_mod_dict = filter_group_dict[meta_filter.filter_type]

        # Any filter value that is a range is represented as just a 'min' and a 'max'. Any singular filter value
        # (ie: corruption, item category, etc) has just an 'option' key
        if isinstance(meta_filter.filter_value, tuple):
            if meta_filter.filter_value[0]:
                meta_mod_dict['min'] = meta_filter.filter_value[0]
            if len(meta_filter.filter_value) >= 2 and meta_filter.filter_value[1]: # len((10,)) = 1 so this is necessary
                meta_mod_dict['max'] = meta_filter.filter_value
        else:
            meta_mod_dict['option'] = meta_filter.filter_value

        if meta_filter.currency_amount:
            if meta_filter.currency_amount[0] is not None:
                meta_mod_dict['min'] = meta_filter.currency_amount[0]
            if meta_filter.currency_amount[1]:
                meta_mod_dict['max'] = meta_filter.currency_amount[1]

def _handle_stats_query(stats_dict, stats_filters_groups: list[StatsFiltersGroup]):
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



