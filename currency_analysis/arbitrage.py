import logging
logger = logging.getLogger(__name__)

import uuid

import networkx as nx
import pandas as pd
from fractions import Fraction

from currency_analysis.data_objects import CurrencyPairMarketData, Currency
from currency_analysis.market_data_capture import MarketDataManager
from currency_analysis.data_management import GoldCostManager


class _CurrencyPairsDataManager:

    def __init__(self, currency_pairs: list[CurrencyPairMarketData]):
        self._currency_pairs = currency_pairs

        self._indexed_dfs = self._build_indexed_dfs(currency_pairs)

    def _build_indexed_dfs(self, currency_pairs: list[CurrencyPairMarketData]) -> dict:
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
                    max_have = (1 / ratio_obj.want_per_have) * ratio_obj.want_supply
                    max_want = ratio_obj.want_supply

                rows['max_have'].append(max_have)
                rows['max_want'].append(max_want)
                rows['prev_cum_have'].append(cum_have)

                cum_have += max_have
                tier += 1

            k = currency_pair.have_currency, currency_pair.want_currency
            indexed_pair_dfs[k] = pd.DataFrame(rows)

        return indexed_pair_dfs

    def fetch_dataframe(self, have_currency: Currency, want_currency: Currency) -> pd.DataFrame:
        k = have_currency, want_currency
        if k not in self._indexed_dfs:
            raise ValueError(f"Could not find {have_currency.value} -> {want_currency.value} dataframe in "
                             f"_CurrencyPairDataManager")

        return self._indexed_dfs[k]


class _ConversionResult:

    def __init__(self,
                 start_currency: Currency,
                 end_currency: Currency,
                 start_supply: float,
                 end_supply: float,
                 average_ratio_used: str):
        self.start_currency = start_currency
        self.end_currency = end_currency
        self.start_supply = start_supply
        self.end_supply = end_supply
        self.average_ratio_used = average_ratio_used

class _CurrencyConverter:

    def __init__(self, currency_pairs_data_manager: _CurrencyPairsDataManager):
        self._data_m = currency_pairs_data_manager

    def _convert_want_per_have_to_str(self, want_per_have: float) -> str:
        base = 1
        if want_per_have == 1:
            want_ratio = base
            have_ratio = base
        elif want_per_have > 1:
            want_ratio = round(want_per_have / base, 2)
            have_ratio = base
        else:
            want_ratio = base
            have_ratio = round(base / want_per_have, 2)

        return f"{want_ratio}:{have_ratio}"


    def convert(self,
                have_currency: Currency,
                want_currency: Currency,
                have_amount: int) -> _ConversionResult:
        neg = have_amount < 0
        have_amount = -have_amount if neg else have_amount

        c_df = self._data_m.fetch_dataframe(have_currency=have_currency,
                                            want_currency=want_currency)
        if c_df.empty:
            raise RuntimeError(f"Found no conversion data for {have_currency} -> {want_currency}")

        used = (
            (have_amount - c_df["prev_cum_have"])
            .clip(lower=0)
            .clip(upper=c_df["max_have"])
        )

        portions = used / used.sum()
        avg_want_per_have = (c_df['want_per_have'] * portions).sum()
        ratio_str = self._convert_want_per_have_to_str(avg_want_per_have)

        want = (used * c_df["want_per_have"]).sum()

        want = -want if neg else want

        result = _ConversionResult(
            start_currency=have_currency,
            end_currency=want_currency,
            start_supply=have_amount,
            end_supply=want,
            average_ratio_used=ratio_str
        )
        return result


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
            'step_end_currency': [],
            'step_start_cost': [],
            'step_end_supply': [],
            'average_ratio': []
        }

        self._profit_data = {
            'cycle_iteration_id': [],
            'divs_profit': [],
            'total_gold_cost': [],
            'gold_per_div_profit': [],
            'end_currency_to_div_conversion_ratio': []
        }

    def add_step(self,
                 cycle_iteration: _CycleIteration,
                 step_num: int,
                 iteration_starting_amount: float,
                 starting_currency: Currency,
                 ending_currency: Currency,
                 starting_amount: float,
                 ending_amount: float,
                 avg_ratio_used: str):
        self._steps_data['cycle_iteration_id'].append(cycle_iteration.id_)
        self._steps_data['iteration_principal'].append(iteration_starting_amount)
        self._steps_data['step_num'].append(step_num)

        self._steps_data['step_start_currency'].append(starting_currency.value)
        self._steps_data['step_end_currency'].append(ending_currency.value)
        self._steps_data['step_start_cost'].append(starting_amount)
        self._steps_data['step_end_supply'].append(ending_amount)
        self._steps_data['average_ratio'].append(avg_ratio_used)

    def add_profit(self,
                   cycle_iteration: _CycleIteration,
                   divs_profit: float,
                   div_conversion_ratio_used: str,
                   total_gold_cost: int):
        self._profit_data['cycle_iteration_id'].append(cycle_iteration.id_)
        self._profit_data['divs_profit'].append(divs_profit)
        self._profit_data['total_gold_cost'].append(total_gold_cost)
        self._profit_data['gold_per_div_profit'].append(total_gold_cost / divs_profit)
        self._profit_data['end_currency_to_div_conversion_ratio'].append(div_conversion_ratio_used)

    def to_dataframe(self) -> pd.DataFrame:
        steps_df = pd.DataFrame(self._steps_data)
        profit_df = pd.DataFrame(self._profit_data)

        df = steps_df.merge(profit_df,
                            how='left',
                            left_on=['cycle_iteration_id'],
                            right_on=['cycle_iteration_id']
                            )
        df = df.sort_values(by=['gold_per_div_profit', 'cycle_iteration_id', 'step_num'],
                            ascending=[True, True, True])

        return df


# Not used for now
class _CycleAnalyzer:

    def __init__(self,
                 currency_converter: _CurrencyConverter,
                 data_tracker: _ArbitrageDataTracker,
                 gold_cost_manager: GoldCostManager):
        self._converter = currency_converter
        self._data_tracker = data_tracker
        self._gold_cost_manager = gold_cost_manager

    def _determine_and_record_profit(self,
                                     cycle_iteration: _CycleIteration,
                                     principal,
                                     pair_objs: list[CurrencyPairMarketData]):
        cum_gold_cost = 0
        prev_supply = principal
        prev_currency = pair_objs[0].have_currency
        for i, pair_obj in enumerate(pair_objs):
            conversion_result = self._converter.convert(
                have_currency=pair_obj.have_currency,
                want_currency=pair_obj.want_currency,
                have_amount=prev_supply
            )
            currency_gold_cost = self._gold_cost_manager.fetch_gold_cost(pair_obj.want_currency)
            total_gold_cost = currency_gold_cost * conversion_result.end_supply
            self._data_tracker.add_step(
                cycle_iteration=cycle_iteration,
                step_num=i + 1,
                iteration_starting_amount=principal,
                starting_amount=prev_supply,
                starting_currency=prev_currency,
                ending_amount=conversion_result.end_supply,
                ending_currency=pair_obj.want_currency,
                avg_ratio_used=conversion_result.average_ratio_used
            )
            cum_gold_cost += total_gold_cost
            prev_currency = pair_obj.want_currency
            prev_supply = conversion_result.end_supply

        profit = prev_supply - principal

        end_currency = pair_objs[-1].want_currency
        if end_currency == Currency.DIVINE_ORB:
            divs_profit = profit
            ratio_used = "1:1"
        else:
            divs_profit_result = self._converter.convert(have_currency=end_currency,
                                                         want_currency=Currency.DIVINE_ORB,
                                                         have_amount=profit)
            divs_profit = divs_profit_result.end_supply
            ratio_used = divs_profit_result.average_ratio_used
        self._data_tracker.add_profit(cycle_iteration=cycle_iteration,
                                      divs_profit=divs_profit,
                                      div_conversion_ratio_used=ratio_used,
                                      total_gold_cost=cum_gold_cost)
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
                 gold_cost_manager: GoldCostManager):
        self._market_data_manager = market_data_manager

        self._data_m = _CurrencyPairsDataManager(currency_pairs=self._market_data_manager.currency_pair_objs)
        self._data_tracker = _ArbitrageDataTracker()
        self._cycle_analyzer = _CycleAnalyzer(
            currency_converter=_CurrencyConverter(currency_pairs_data_manager=self._data_m),
            data_tracker=self._data_tracker,
            gold_cost_manager=gold_cost_manager
        )

    def _verify_currency_pairs(self):
        currency_pair_objs = self._market_data_manager.currency_pair_objs
        all_currencies = {c for p in currency_pair_objs for c in (p.have_currency, p.want_currency)}
        to_div_currencies = {p.have_currency for p in currency_pair_objs
                             if p.want_currency == Currency.DIVINE_ORB}
        missing_currencies = all_currencies - to_div_currencies
        missing_currencies = missing_currencies - {Currency.DIVINE_ORB}

        if missing_currencies:
            raise RuntimeError(f"Missing 'currency' -> 'divine orb' for: {missing_currencies}")


    def _create_graph(self) -> nx.DiGraph:
        G = nx.DiGraph()

        for pair_obj in self._market_data_manager.currency_pair_objs:
            if not pair_obj.sorted_ratios:
                continue

            G.add_edge(
                pair_obj.have_currency,
                pair_obj.want_currency,
                pair_obj=pair_obj
            )

        return G

    def arbitrage(self) -> pd.DataFrame:
        self._verify_currency_pairs()

        G = self._create_graph()
        cycle_objs = [_Cycle(simple_cycle, graph=G) for simple_cycle in nx.simple_cycles(G=G, length_bound=5)]
        for i, cycle in enumerate(cycle_objs):
            logger.info(f"Analyzing cycle {i} of {len(cycle_objs)} ({i / len(cycle_objs)})")
            self._cycle_analyzer.analyze_and_record_cycle_profit(cycle)
            
        df = self._data_tracker.to_dataframe()

        return df
