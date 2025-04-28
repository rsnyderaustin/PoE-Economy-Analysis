
from enum import Enum


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


def _fill_in_min_max(relevant_dict: dict, values_range: tuple):
    min_val = values_range[0]
    max_val = values_range[1]

    relevant_dict[MiscSearchParameter.MIN.value] = min_val
    relevant_dict[MiscSearchParameter.MAX.value] = max_val


def _handle_meta_query(query_dict, meta_filters_groups: list[MetaFiltersGroup] = None):
    query_dict[MiscSearchParameter.FILTERS.value] = dict()
    meta_query = query_dict[MiscSearchParameter.FILTERS.value]
    for meta_filters_group in meta_filters_groups:
        if meta_filters_group.search_type not in MetaSearchType:
            raise ValueError(f"Enum {meta_filters_group.search_type} not in acceptable "
                             f"enums {MetaSearchType}.")

        if meta_filters_group.search_type.value in meta_query:
            raise RuntimeError(f"Attempted to add enum {meta_filters_group.search_type.value} to query when"
                               f"it's already present.")

        meta_query[meta_filters_group.search_type.value] = dict()
        filter_group_dict = meta_query[meta_filters_group.search_type.value]

        filter_group_dict[MiscSearchParameter.FILTERS.value] = dict()
        filter_group_dict = filter_group_dict[MiscSearchParameter.FILTERS.value]

        for meta_mod_filter in meta_filters_group.meta_mod_filters:
            filter_group_dict[meta_mod_filter.meta_mod_name_enum.value] = dict()
            meta_mod_dict = filter_group_dict[meta_mod_filter.meta_mod_name_enum.value]

            if isinstance(meta_mod_filter.mod_value, tuple):
                _fill_in_min_max(relevant_dict=meta_mod_dict,
                                 values_range=meta_mod_filter.mod_value)
            else:
                meta_mod_dict[MiscSearchParameter.OPTION.value] = meta_mod_filter.mod_value


def _handle_stats_query(query_dict, stats_filters_groups: list[StatsFiltersGroup] = None):
    query_dict[MiscSearchParameter.STATS.value] = dict()
    stats_dict = query_dict[MiscSearchParameter.STATS.value]

    if not stats_filters_groups:
        stats_dict[0] = {
            MiscSearchParameter.FILTERS.value: [],
            MiscSearchParameter.TYPE.value: StatFilterType.AND.value
        }

        return

    # Each StatsFiltersGroup is a group with a type such as AND, IF, WEIGHTED_SUMV2, etc that possibly
    # holds individual mod filters
    for i, stats_filters_group in enumerate(stats_filters_groups):
        if stats_filters_group.filter_type not in StatFilterType:
            raise ValueError(f"FilterType {stats_filters_group.filter_type} not one of acceptable "
                             f"FilterTypes {StatFilterType}.")

        stats_dict[MiscSearchParameter.TYPE.value] = stats_filters_group.filter_type.value

        # Take care of the overall stats group value range (for weightedV2, count, etc)
        if stats_filters_group.value_range:
            stats_dict[MiscSearchParameter.VALUE.value] = {

            }
            value_dict = stats_dict[MiscSearchParameter.VALUE.value]
            if stats_filters_group.value_range[0]:
                value_dict[MiscSearchParameter.MIN.value] = stats_filters_group.value_range[0]
            if stats_filters_group.value_range[1]:
                value_dict[MiscSearchParameter.MAX.value] = stats_filters_group.value_range[1]

        """
        Can't really tell yet when this is needed vs not
        stats_dict[i] = {
            MiscSearchParameter.DISABLED.value: False
        }"""

        # Take care of inserting individual mods within the stats group
        if stats_filters_group.mod_filters:
            stats_dict[MiscSearchParameter.FILTERS.value] = dict()
            mod_filters_dict = stats_dict[MiscSearchParameter.FILTERS.value]

            for i, mod_filter in enumerate(stats_filters_group.mod_filters):
                mod_filters_dict[i] = {
                    MiscSearchParameter.ID.VALUE: mod_filter.mod_enum.value
                }

                if mod_filter.values_range or mod_filter.weight:
                    mod_filters_dict[i][MiscSearchParameter.VALUE.value] = dict()
                    mod_values_dict = mod_filters_dict[i][MiscSearchParameter.VALUE.value]

                    if mod_filter.values_range:
                        _fill_in_min_max(relevant_dict=mod_values_dict,
                                         values_range=mod_filter.values_range)
                    if mod_filter.weight:
                        mod_values_dict[MiscSearchParameter.WEIGHT.value] = mod_filter.weight


class TradeQueryConstructor:

    filter_format = {

    }

    @classmethod
    def create_trade_query(cls,
                           meta_filters_groups: list[MetaFiltersGroup] = None,
                           stats_filters_groups: list[StatsFiltersGroup] = None,
                           league: str = "Dawn of the Hunt"):

        returnable_query = {
            'query': {
                MiscSearchParameter.STATUS.value:
                    {MiscSearchParameter.OPTION.value: 'online'}
            }
        }
        query = returnable_query['query']

        _handle_meta_query(query_dict=query,
                           meta_filters_groups=meta_filters_groups)

        _handle_stats_query(query_dict=returnable_query,
                            stats_filters_groups=stats_filters_groups)
        return returnable_query



