from utils.enums import (MetaSearchType, StatSearchType, EquipmentAttribute,
                         WeaponAttribute, ArmourAttribute, TypeFilters, RequirementFilters, MiscFilters, TradeFilters)
from .meta_filters_group import MetaModFilter
from .stats_filters_group import StatsFiltersGroup


def _handle_min_max(relevant_dict: dict, meta_mod_filter: MetaModFilter):
    min_val = meta_mod_filter.mod_value[0]
    max_val = meta_mod_filter.mod_value[1]

    if meta_mod_filter.price_currency_enum:
        relevant_dict['option'] = meta_mod_filter.price_currency_enum.value

    if min_val:
        relevant_dict['min'] = min_val

    if max_val:
        relevant_dict['max'] = max_val


class TradeQueryConstructor:

    _meta_filter_to_search_type = {
        **{
            enum: MetaSearchType.TYPE
            for enum in TypeFilters
        },
        **{
            enum: MetaSearchType.EQUIPMENT
            for enum in list(EquipmentAttribute) + list(WeaponAttribute) + list(ArmourAttribute)
        },
        **{
            enum: MetaSearchType.REQUIREMENT
            for enum in RequirementFilters
        },
        **{
            enum: MetaSearchType.MISC
            for enum in MiscFilters
        },
        **{
            enum: MetaSearchType.TRADE
            for enum in TradeFilters
        }
    }

    def __init__(self):
        self.query = {
            'query': {
                'status': {'option': 'online'}
            }
        }

    def create_trade_query(self,
                           meta_mod_filters: list[MetaModFilter] = None,
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

    def _handle_meta_query(self, meta_mod_filters: list[MetaModFilter]):
        self.query['query']['filters'] = dict()
        meta_query = self.query['query']['filters']
        for meta_filter in meta_mod_filters:
            meta_filter_group = self.__class__._meta_filter_to_search_type[meta_filter.meta_filter_enum].value

            if meta_filter_group not in meta_query:
                meta_query[meta_filter_group] = dict()
                meta_query[meta_filter_group]['filters'] = dict()

            filter_group_dict = meta_query[meta_filter_group]['filters']

            filter_group_dict[meta_filter.meta_filter_enum.value] = dict()
            meta_mod_dict = filter_group_dict[meta_filter.meta_filter_enum.value]

            if isinstance(meta_filter.mod_value, tuple):
                _handle_min_max(relevant_dict=meta_mod_dict,
                                meta_mod_filter=meta_filter)
            else:
                meta_mod_dict['option'] = meta_filter.mod_value

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
                                            values_range=mod_filter.values_range)
                        if mod_filter.weight:
                            mod_values_dict['weight'] = mod_filter.weight



