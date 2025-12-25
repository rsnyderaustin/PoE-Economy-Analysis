import logging
import uuid

import networkx as nx
import pandas as pd

from currency_analysis.market_data_capture import MarketDataManager
from currency_analysis.data_objects import CurrencyPair


class _CurrencyPairsDataManager:

    def __init__(self,
                 logger: logging.Logger,
                 currency_pairs: list[CurrencyPair]):
        self._logger = logger
        self._currency_pairs = currency_pairs

        self._indexed_dfs = self._build_indexed_dfs(currency_pairs)

    def _build_indexed_dfs(self, currency_pairs: list[CurrencyPair]) -> dict:
        indexed_pair_dfs = dict()
        for currency_pair in currency_pairs:
            rows = {
                'have_currency': [],
                'want_currency': [],
                'tier': [],
                'want_per_have': [],
                'max_have': [],
                'prev_cum_have': [],
                'max_want': []
            }

            tier = 0
            cum_have = 0
            for i, ratio_obj in enumerate(currency_pair.sorted_ratios):
                rows['have_currency'].append(currency_pair.have_currency)
                rows['want_currency'].append(currency_pair.want_currency)
                rows['tier'].append(tier)
                rows['want_per_have'].append(ratio_obj.want_per_have)

                # For the worst posted ratio, we just assume an infinite supply
                if i == len(currency_pair.sorted_ratios) - 1:
                    max_have = 999e3
                    max_want = 999e3
                else:
                    max_have = (1 / ratio_obj.want_per_have) * ratio_obj.supply
                    max_want = ratio_obj.supply

                rows['max_have'].append(max_have)
                rows['max_want'].append(max_want)
                rows['prev_cum_have'] = cum_have

                cum_have += max_have

                cum_have += ratio_obj.supply
                tier += 1

            k = currency_pair.have_currency, currency_pair.want_currency
            indexed_pair_dfs[k] = pd.DataFrame(rows)

        return indexed_pair_dfs

    def fetch_dataframe(self, have_currency: str, want_currency: str) -> pd.DataFrame:
        k = have_currency, want_currency
        if k not in self._indexed_dfs:
            raise ValueError(f"Could not find {have_currency} -> {want_currency} dataframe in "
                             f"_CurrencyPairDataManager")

        return self._indexed_dfs[k]


class _CurrencyConverter:

    def __init__(self,
                 currency_pairs_data_manager: _CurrencyPairsDataManager,
                 logger: logging.Logger):
        self._logger = logger
        self._data_m = currency_pairs_data_manager

    def convert(self,
                have_currency: str,
                want_currency: str,
                have_amount: int) -> float:
        c_df = self._data_m.fetch_dataframe(have_currency=have_currency,
                                            want_currency=want_currency)
        if c_df.empty:
            raise RuntimeError(f"Found no conversion data for {have_currency} -> {want_currency}")

        used = (
            (have_amount - c_df["prev_cum_have"])
            .clip(lower=0)
            .clip(upper=c_df["max_have"])
        )

        want = (used * c_df["want_per_have"]).sum()
        return want


class _Cycle:
    def __init__(self, nodes, graph):
        self.nodes = nodes

        self.currency_pair_objects = [
            graph[u][v]["pair_obj"]
            for u, v in zip(nodes, nodes[1:] + [nodes[0]])
        ]

        self.start_currency = self.currency_pair_objects[0].have_currency
        self.end_currency = self.currency_pair_objects[-1].want_currency

        self._starting_amounts = None

    @property
    def test_principals(self) -> list:
        first_step_buyout = self.currency_pair_objects[0].determine_total_buyout_cost()
        return [
            first_step_buyout * 0.05,
            first_step_buyout * 0.1,
            first_step_buyout * 0.25,
            first_step_buyout * 0.5,
            first_step_buyout * 0.75,
            first_step_buyout,
            first_step_buyout * 1.25
        ]

    @property
    def feasibility_principal(self) -> float:
        return max(1, self.currency_pair_objects[0].determine_total_buyout_cost() * 0.05)


class _CycleIteration:

    def __init__(self, cycle: _Cycle, principal: int | float):
        self.id_ = uuid.uuid4()

        self.cycle = cycle
        self.principal = principal


class _ArbitrageDataTracker:

    def __init__(self):
        self._steps_data = {
            'cycle_iteration_id': [],
            'iteration_principal': [],
            'step_num': [],
            'step_start_currency': [],
            'step_start_cost': [],
            'step_end_currency': [],
            'step_end_supply': []
        }

        self._profit_data = {
            'cycle_iteration_id': [],
            'divs_profit': []
        }

    def add_step(self,
                 cycle_iteration: _CycleIteration,
                 step_num: int,
                 iteration_starting_amount: float,
                 starting_currency: str,
                 starting_amount: float,
                 ending_currency: str,
                 ending_amount: float):
        self._steps_data['cycle_iteration_id'].append(cycle_iteration.id_)
        self._steps_data['iteration_principal'].append(iteration_starting_amount)
        self._steps_data['step_num'].append(step_num)

        self._steps_data['step_start_currency'].append(starting_currency)
        self._steps_data['step_start_cost'].append(starting_amount)
        self._steps_data['step_end_currency'].append(ending_currency)
        self._steps_data['step_end_supply'].append(ending_amount)

    def add_profit(self, cycle_iteration: _CycleIteration, divs_profit: float):
        self._profit_data['cycle_iteration_id'].append(cycle_iteration.id_)
        self._profit_data['divs_profit'].append(divs_profit)

    def to_dataframe(self) -> pd.DataFrame:
        steps_df = pd.DataFrame(self._steps_data)
        profit_df = pd.DataFrame(self._profit_data)

        df = steps_df.merge(profit_df,
                            how='left',
                            left_on=['cycle_iteration_id'],
                            right_on=['cycle_iteration_id']
                            )

        return df


# Not used for now
class _CycleAnalyzer:

    def __init__(self,
                 currency_converter: _CurrencyConverter,
                 data_tracker: _ArbitrageDataTracker,
                 logger: logging.Logger):
        self._converter = currency_converter
        self._data_tracker = data_tracker
        self._logger = logger

    def _determine_and_record_profit(self,
                                     cycle_iteration: _CycleIteration,
                                     principal,
                                     pair_objs: list[CurrencyPair]):
        prev_supply = principal
        prev_currency = pair_objs[0].have_currency
        for i, pair_obj in enumerate(pair_objs):
            conversion_amount = self._converter.convert(
                have_currency=pair_obj.have_currency,
                want_currency=pair_obj.want_currency,
                have_amount=prev_supply
            )
            self._data_tracker.add_step(
                cycle_iteration=cycle_iteration,
                step_num=i + 1,
                iteration_starting_amount=principal,
                starting_amount=prev_supply,
                starting_currency=prev_currency,
                ending_amount=conversion_amount,
                ending_currency=pair_obj.want_currency
            )
            prev_currency = pair_obj.want_currency
            prev_supply = conversion_amount

        profit = prev_supply - principal

        end_currency = pair_objs[-1].want_currency
        if end_currency == 'divine orb':
            divs_profit = profit
        else:
            divs_profit = self._converter.convert(have_currency=end_currency,
                                                  want_currency='divine orb',
                                                  have_amount=profit)
        self._data_tracker.add_profit(cycle_iteration=cycle_iteration,
                                      divs_profit=divs_profit)
        return divs_profit

    def analyze_and_record_cycle_profit(self, cycle: _Cycle):
        feasibility_profit = self._determine_and_record_profit(cycle_iteration=_CycleIteration(cycle=cycle,
                                                                                               principal=cycle.feasibility_principal),
                                                               principal=cycle.feasibility_principal,
                                                               pair_objs=cycle.currency_pair_objects)
        if feasibility_profit < 0:
            return self._data_tracker

        for test_cost in cycle.test_principals:
            self._determine_and_record_profit(cycle_iteration=_CycleIteration(cycle=cycle,
                                                                              principal=test_cost),
                                              principal=test_cost,
                                              pair_objs=cycle.currency_pair_objects)


class CurrencyArbitrager:

    def __init__(self,
                 market_data_manager: MarketDataManager,
                 logger: logging.Logger):
        self._market_data_manager = market_data_manager
        self._logger = logger

        self._currency_pair_objs = self._market_data_manager.fetch_currency_pair_objs()
        self._data_m = _CurrencyPairsDataManager(currency_pairs=self._currency_pair_objs,
                                                 logger=logger)
        self._data_tracker = _ArbitrageDataTracker()
        self._cycle_analyzer = _CycleAnalyzer(
            currency_converter=_CurrencyConverter(
                currency_pairs_data_manager=self._data_m,
                logger=logger
            ),
            data_tracker=self._data_tracker,
            logger=logger
        )

    def _verify_currency_pairs(self):
        all_currencies = {c for p in self._currency_pair_objs for c in (p.have_currency, p.want_currency)}
        to_div_currencies = {p.have_currency for p in self._currency_pair_objs
                             if p.want_currency == 'divine orb'}
        missing_currencies = all_currencies - to_div_currencies
        missing_currencies = missing_currencies - {'divine orb'}

        if missing_currencies:
            raise RuntimeError(f"Missing 'currency' -> 'divine orb' for: {missing_currencies}")


    def _build_graph(self) -> nx.DiGraph:
        G = nx.DiGraph()

        for pair_obj in self._currency_pair_objs:
            G.add_edge(
                pair_obj.have_currency,
                pair_obj.want_currency,
                pair_obj=pair_obj
            )

        return G

    def arbitrage(self) -> pd.DataFrame:
        self._verify_currency_pairs()

        G = self._build_graph()
        cycle_objs = [_Cycle(simple_cycle, graph=G) for simple_cycle in nx.simple_cycles(G=G, length_bound=5)]
        for i, cycle in enumerate(cycle_objs):
            self._logger.info(f"Analyzing cycle {i} of {len(cycle_objs)} ({i / len(cycle_objs)})")
            self._cycle_analyzer.analyze_and_record_cycle_profit(cycle)
            
        return self._data_tracker.to_dataframe()

