import logging
import math
import pprint
import pandas as pd

from currency_analysis.market_data_capture import MarketDataManager, RatioSupply, CurrencyPairRates

import networkx as nx


class _CurrencyConverter:

    def __init__(self,
                 currency_pair_rates: list[CurrencyPairRates],
                 logger: logging.Logger):
        self._logger = logger

        self._df = self._build_df(currency_pair_rates=currency_pair_rates)

    def _build_df(self, currency_pair_rates: list[CurrencyPairRates]) -> pd.DataFrame:
        ratios = dict()
        for pair_rates in currency_pair_rates:
            d = pair_rates.grouped_d
            k = r.have_currency, r.want_currency
            if k not in ratios:
                ratios[k] = list()
            ratios[k].append(r)

        for currencies, ratio_objs in ratios.items():
            ratios[currencies] = sorted(ratio_objs, key=lambda r: r.want_per_have)

        rows = {
            'have_currency': [],
            'want_currency': [],
            'tier': [],
            'want_per_have': [],
            'max_have': [],
            'prev_cum_have': [],
            'max_want': []
        }
        for (have_currency, want_currency), ratio_objs in ratios.items():
            tier = 0
            cum_have = 0
            for i, ratio_obj in enumerate(ratio_objs):
                rows['have_currency'].append(have_currency)
                rows['want_currency'].append(want_currency)
                rows['tier'].append(tier)
                rows['want_per_have'].append(ratio_obj.want_per_have)

                # For the worst posted ratio, but we just assume an infinite supply
                if i == len(ratio_objs) - 1:
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

        return pd.DataFrame(rows)

    def convert(self,
                have_currency: str,
                want_currency: str,
                have_amount: int) -> float:
        c_df = self._df[
            (self._df['have_currency'] == have_currency) &
            (self._df['want_currency'] == want_currency)
        ]
        if c_df.empty:
            raise RuntimeError(f"Found no conversion data for {have_currency} -> {want_currency}")

        used = (
            (have_amount - c_df["prev_cum_have"])
            .clip(lower=0)
            .clip(upper=c_df["max_have"])
        )

        want = (used * c_df["want_per_have"]).sum()
        return want


class _GraphCycle:

    def __init__(self, cycle_nodes: list):
        self._nodes = cycle_nodes

    def determine_cost_to_reach_worst_ratio(self) -> float:
        """
        Determines what the initial cycle supply is to reach the worst ratio on any one of the trades.
        :return:
        """

        """
        Essentially all this function does is algorithmically determines what our limiting factor 
        (currency) is
        """

        pair_objs = [node.pair_obj for node in self._nodes]

        for p in pair_objs:
            if 'cost_to_reach_worst_tier' not in p.atts:
                p.atts['cost_to_reach_worst_tier'] = sum(r.buyout_cost for r in p.sorted_ratios[:-1])

            if 'supply_til_worst_tier' not in p.atts:
                p.atts['supply_til_worst_tier'] = sum(r.supply for r in p.sorted_ratios[:-1])

        table_rows = {
            'have_currency': [p.have_currency for p in pair_objs],
            'want_currency': [p.want_currency for p in pair_objs],
            'buyout_cost': [p.atts['cost_to_reach_worst_tier'] for p in pair_objs],
            'buyout_supply': [p.atts['supply_til_worst_tier'] for p in pair_objs]
        }
        df = pd.DataFrame(table_rows)
        df['buyout_ratio'] = (df['buyout_supply'].shift(1) / df['buyout_cost']).fillna(1)

        limiting_ratio = min(df['buyout_ratio'])
        pass


class _ProfitResults:

    def __init__(self, pair_objs: list[CurrencyPairRates]):
        self._pair_objs = pair_objs

        self._data = dict()

    def add_results(self, starting_amount: float, divs_profit: float):
        self._data[starting_amount] = divs_profit

class CurrencyArbitrager:

    def __init__(self,
                 market_data_manager: MarketDataManager,
                 logger: logging.Logger):
        self._market_data_manager = market_data_manager
        self._currency_pair_objs = self._market_data_manager.fetch_currency_pair_objs()

        self._converter = _CurrencyConverter(currency_pair_rates=self._market_data_manager.fetch_currency_pair_objs(),
                                             logger=logger)

    def determine_missing_trade_records(self) -> list[dict]:
        all_currencies = {c for p in self._currency_pair_objs for c in (p.have_currency, p.want_currency)}
        to_div_currencies = {p.have_currency for p in self._currency_pair_objs
                             if p.want_currency == 'divine orb'}
        missing_currencies = all_currencies - to_div_currencies
        missing_currencies = missing_currencies - {'divine orb'}

        return [{'have': missing_c,
                 'want': 'divine orb'} for missing_c in missing_currencies]

    def _build_graph(self) -> nx.DiGraph:
        G = nx.DiGraph()

        pair_objs = self._market_data_manager.fetch_currency_pair_objs()
        for pair_obj in pair_objs:
            G.add_edge(
                pair_obj.have_currency,
                pair_obj.want_currency,
                pair_obj=pair_obj
            )

        return G

    def _determine_profit(self, initial_cost, pair_objs: list[CurrencyPairRates]):
        last_supply = initial_cost
        for pair_obj in pair_objs:
            conversion_amount = self._converter.convert(
                have_currency=pair_obj.have_currency,
                want_currency=pair_obj.want_currency,
                have_amount=last_supply
            )
            last_supply = conversion_amount

        profit = last_supply - initial_cost
        divs_profit = self._converter.convert(have_currency=pair_objs[-1].want_currency,
                                              want_currency='divine orb',
                                              have_amount=profit)
        return divs_profit

    def determine_profitability(self, nodes) -> _ProfitResults:
        results = _ProfitResults(pair_objs=self._currency_pair_objs)

        pair_objs = [node.pair_obj for node in nodes]
        cost_basis = pair_objs[0].determine_total_buyout_cost()

        feasibility_cost = cost_basis * 0.05
        profit = self._determine_profit(initial_cost=feasibility_cost,
                                        pair_objs=pair_objs)
        if profit < 0:
            results.add_results(starting_amount=feasibility_cost,
                                divs_profit=profit)
            return results

        test_costs = [
            cost_basis * 0.05,
            cost_basis * 0.1,
            cost_basis * 0.25,
            cost_basis * 0.5,
            cost_basis * 0.75,
            cost_basis,
            cost_basis * 1.25
        ]

        for test_cost in test_costs:
            profit = self._determine_profit(initial_cost=test_cost,
                                            pair_objs=pair_objs)
            results.add_results(starting_amount=test_cost,
                                divs_profit=profit)

        return results


    def arbitrage(self):
        missing_trade_records = self.determine_missing_trade_records()
        if missing_trade_records:
            raise RuntimeError(
                "Missing trade records:\n"
                f"{pprint.pformat(missing_trade_records)}"
            )

        G = self._build_graph()
        self._determine_profitability(G=G)

