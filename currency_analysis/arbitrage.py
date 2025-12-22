import logging
import math
import pprint
import pandas as pd

from currency_analysis.market_data_capture import MarketDataManager, RatioSupply

import networkx as nx


class _CurrencyConverter:

    def __init__(self,
                 ratio_objs: list[RatioSupply],
                 logger: logging.Logger):
        self._logger = logger

        self._df = self._build_df(ratio_objs=ratio_objs)

    def _build_df(self, ratio_objs) -> pd.DataFrame:
        ratios = dict()
        for r in ratio_objs:
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


class CurrencyArbitrager:

    def __init__(self,
                 market_data_manager: MarketDataManager,
                 logger: logging.Logger):
        self._market_data_manager = market_data_manager
        self._ratio_objs = self._market_data_manager.fetch_data()

        self._converter = _CurrencyConverter(ratio_objs=self._ratio_objs,
                                             logger=logger)

    def determine_missing_trade_records(self) -> list[dict]:
        all_currencies = {c for r in self._ratio_objs for c in (r.have_currency, r.want_currency)}
        to_div_currencies = {r.have_currency for r in self._ratio_objs if r.want_currency == 'divine orb'}
        missing_currencies = all_currencies - to_div_currencies
        missing_currencies = missing_currencies - {'divine orb'}

        return [{'have': missing_c,
                 'want': 'divine orb'} for missing_c in missing_currencies]

    def _build_graph(self) -> nx.DiGraph():
        g = nx.DiGraph()

        ratio_objs = self._market_data_manager.fetch_data()
        for ratio_obj in ratio_objs:
            g.add_edge(
                ratio_obj.have_currency,
                ratio_obj.want_currency,
                weight=-math.log(ratio_obj.haves_per_want)
            )

        return g

    def _convert_to_divs(self, currency: str, amount: int):


    def _determine_profitability(self, graph: nx.DiGraph):
        cycles = list(nx.simple_cycles(G=graph,
                                       length_bounds=5))

        G = graph
        for cycle in cycles:
            prod_rate = 1

            edge_supplies = []
            for i in range(len(cycle)):
                src = cycle[i]
                dst = cycle[(i + 1) % len(cycle)]
                edge_data = G[src][dst]  # assuming single edge for now
                rate = edge_data['rate']
                supply = edge_data.get('available_B', float('inf'))  # or however supply is stored
                prod_rate *= rate
                edge_supplies.append(supply)

            # Max quantity feasible = min(edge supplies)
            max_qty = min(edge_supplies)

            # Profit multiplier = final / initial
            profit_multiplier = prod_rate
            net_profit_per_unit = profit_multiplier - 1  # can also subtract fees if applicable

    def arbitrage(self):
        missing_trade_records = self.determine_missing_trade_records()

        if missing_trade_records:
            raise RuntimeError(
                "Missing trade records:\n"
                f"{pprint.pformat(missing_trade_records)}"
            )

        g = self._build_graph()
        cycles = nx.negative_edge_cycle(g, weight="weight")

