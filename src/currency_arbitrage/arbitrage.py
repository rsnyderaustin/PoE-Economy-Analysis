import logging

from src.currency_arbitrage import utils

logger = logging.getLogger(__name__)

import networkx as nx
import pandas as pd

from src.currency_arbitrage.data_objects import CurrencyPairMarketData, Currency, ExchangeRatio
from src.currency_arbitrage.market_data_capture import MarketDataManager
from src.currency_arbitrage.data_management import GoldCostManager


class _ConversionResult:

    def __init__(self,
                 start_currency: Currency,
                 end_currency: Currency,
                 start_supply: float,
                 end_supply: float,
                 average_ratio_used: ExchangeRatio):
        self.start_currency = start_currency
        self.end_currency = end_currency
        self.start_supply = start_supply
        self.end_supply = end_supply
        self.average_ratio_used = average_ratio_used


class _CurrencyConverter:

    def __init__(self, currency_pair_objects: list[CurrencyPairMarketData]):
        self._dfs = self._build_indexed_dfs(currency_pairs=currency_pair_objects)

    def _build_indexed_dfs(self, currency_pairs: list[CurrencyPairMarketData]) -> dict:
        indexed_pair_dfs = dict()
        for currency_pair in currency_pairs:
            if not currency_pair.sorted_ratios:
                continue

            rows = {
                'have_currency': [],
                'want_currency': [],
                'tier': [],
                'want_per_have': [],
                'max_have': [],
                'prev_cum_have': [],
                'max_want': []
            }

            cum_have = 0
            for tier, ratio_obj in enumerate(currency_pair.sorted_ratios):
                rows['have_currency'].append(currency_pair.have_currency)
                rows['want_currency'].append(currency_pair.want_currency)
                rows['tier'].append(tier)
                rows['want_per_have'].append(ratio_obj.want_per_have)
                max_have = (1 / ratio_obj.want_per_have) * ratio_obj.want_supply
                rows['max_have'].append(max_have)
                rows['max_want'].append(ratio_obj.want_supply)
                rows['prev_cum_have'].append(cum_have)

                cum_have += max_have

            # We add a final ratio that represents the non-analyzed ratios and supplies
            rows['have_currency'].append(currency_pair.have_currency)
            rows['want_currency'].append(currency_pair.want_currency)
            rows['tier'].append(len(currency_pair.sorted_ratios))
            want_per_have = currency_pair.sorted_ratios[-1].want_per_have * 0.99
            rows['want_per_have'].append(want_per_have)
            rows['max_have'].append(99e5)
            rows['max_want'].append(99e5)
            rows['prev_cum_have'].append(cum_have)

            k = currency_pair.have_currency, currency_pair.want_currency
            indexed_pair_dfs[k] = pd.DataFrame(rows)

        return indexed_pair_dfs

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
                have_amount: float) -> _ConversionResult:
        neg = have_amount < 0
        have_amount = -have_amount if neg else have_amount

        c_df = self._dfs[have_currency, want_currency]
        if c_df.empty:
            raise RuntimeError(f"Found no conversion data for {have_currency} -> {want_currency}")

        used = (
            (have_amount - c_df["prev_cum_have"])
            .clip(lower=0)
            .clip(upper=c_df["max_have"])
        )

        portions = used / used.sum()
        avg_want_per_have = (c_df['want_per_have'] * portions).sum()
        avg_ratio_used = ExchangeRatio(
            raw_ratio=self._convert_want_per_have_to_str(avg_want_per_have),
            have_currency=have_currency,
            want_currency=want_currency,
            want_per_have=avg_want_per_have
        )

        want = (used * c_df["want_per_have"]).sum()
        want = -want if neg else want

        result = _ConversionResult(
            start_currency=have_currency,
            end_currency=want_currency,
            start_supply=have_amount,
            end_supply=want,
            average_ratio_used=avg_ratio_used
        )
        return result


class _CycleIterationStep:

    def __init__(self,
                 step_num: int,
                 have_currency: Currency,
                 want_currency: Currency,
                 have_cost: float,
                 want_supply: float,
                 gold_cost: float,
                 average_ratio_used: ExchangeRatio):
        self.step_num = step_num
        self.have_currency = have_currency
        self.want_currency = want_currency
        self.have_cost = have_cost
        self.want_supply = want_supply
        self.gold_cost = gold_cost
        self.average_ratio_used = average_ratio_used

    def to_dict(self) -> dict:
        return utils.standard_to_dict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "_CycleIterationStep":
        d['have_currency'] = Currency(d['have_currency'])
        d['want_currency'] = Currency(d['want_currency'])
        d['average_ratio_used'] = ExchangeRatio.from_dict(d['average_ratio_used'])
        return _CycleIterationStep(**d)


class _CycleIterationResult:

    def __init__(self,
                 divs_profit: float,
                 total_gold_cost: float,
                 to_div_ratio: ExchangeRatio):
        self.divs_profit = divs_profit
        self.total_gold_cost = total_gold_cost
        self.to_div_ratio = to_div_ratio

    def to_dict(self) -> dict:
        return utils.standard_to_dict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "_CycleIterationResult":
        d['to_div_ratio'] = ExchangeRatio.from_dict(d['to_div_ratio'])
        return _CycleIterationResult(**d)

    @property
    def gold_per_div_profit(self) -> float:
        return self.total_gold_cost / self.divs_profit


class _CycleIteration:

    def __init__(self,
                 principal: int | float,
                 currencies_order: list[Currency],
                 steps: list[_CycleIterationStep] | None = None,
                 result: _ConversionResult | None = None):
        self.principal = principal
        self.currencies_order = currencies_order

        self.steps: list[_CycleIterationStep] = steps or []

        self.result: _CycleIterationResult | None = result or None

    def __key(self):
        return tuple(self.currencies_order), round(float(self.principal), 2)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        if not isinstance(other, _CycleIteration):
            return NotImplemented

        return self.__key() == other.__key()

    def to_dict(self) -> dict:
        return utils.standard_to_dict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "_CycleIteration":
        d['steps'] = [_CycleIterationStep.from_dict(step_d) for step_d in d['steps']]
        d['result'] = _CycleIterationResult.from_dict(d['result']) if d['result'] else None

        return _CycleIteration(**d)

    @property
    def total_gold_cost(self) -> float:
        return sum(step.gold_cost for step in self.steps)

    def __str__(self) -> str:
        strings = []
        for i, step in enumerate(self.steps):
            strings.append(f"\nStep {i}:"
                           f"\n\tCurrencies: {round(step.have_cost, 2)} {step.have_currency.value} "
                           f"-> {round(step.want_supply, 2)} {step.want_currency.value}"
                           f"\n\tWant:Have ratio: {step.average_ratio_used.raw_ratio}")

        return ''.join(strings)


class _Cycle:
    def __init__(self, nodes: list, graph: nx.DiGraph):
        self.nodes = nodes

        self.currency_pair_objects = [
            graph[u][v]["pair_obj"]
            for u, v in zip(nodes, nodes[1:] + [nodes[0]])
        ]

        self.endpoint_currency = self.currency_pair_objects[0].have_currency

        self.iterations: list[_CycleIteration] = []

    @property
    def currencies_order(self) -> list[Currency]:
        currencies = [self.endpoint_currency]
        currencies.extend(
            [pair_obj.want_currency for pair_obj in self.currency_pair_objects]
        )
        return currencies

    def __key(self):
        return tuple(self.currencies_order)

    def __hash__(self):
        return hash(self.__key())


class _CyclesIterationsFactory:

    @classmethod
    def create_cycle_iterations(cls, cycle: _Cycle) -> list[_CycleIteration]:
        first_currency_pair_obj = cycle.currency_pair_objects[0]
        buyout_cost = first_currency_pair_obj.determine_total_buyout_cost()
        principals = [int(buyout_cost * portion) for portion in [0.05, 0.1, 0.25, 0.5, 0.75, 1.25]]
        principals = [p for p in principals if p > 1]
        return [_CycleIteration(principal=principal,
                                currencies_order=cycle.currencies_order) for principal in principals]

"""class _ArbitrageDataTracker:

    def __init__(self):
        self._steps_data = {
            'cycle_iteration_id': [],
            'iteration_principal': [],
            'step_num': [],
            'have': [],
            'want': [],
            'have_cost': [],
            'want_supply': [],
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

        self._steps_data['have'].append(starting_currency.value)
        self._steps_data['want'].append(ending_currency.value)
        self._steps_data['have_cost'].append(starting_amount)
        self._steps_data['want_supply'].append(ending_amount)
        self._steps_data['average_ratio'].append(avg_ratio_used)

    def add_profit(self,
                   cycle_iteration_result: _CycleIterationResult):
        self._profit_data['cycle_iteration_id'].append(cycle_iteration_result.cycle_iteration.id_)
        self._profit_data['divs_profit'].append(cycle_iteration_result.divs_profit)
        self._profit_data['total_gold_cost'].append(cycle_iteration_result.total_gold_cost)
        self._profit_data['gold_per_div_profit'].append(cycle_iteration_result.gold_per_div_profit)
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

        return df"""


class _CycleIterationStepper:

    def __init__(self,
                 currency_converter: _CurrencyConverter,
                 gold_cost_manager: GoldCostManager):
        self._converter = currency_converter
        self._gold_cost_manager = gold_cost_manager

    def step_through_cycle_iteration(self,
                                     cycle_iteration: _CycleIteration,
                                     currency_pair_objects: list[CurrencyPairMarketData]):
        steps = cycle_iteration.steps
        for i, pair_obj in enumerate(currency_pair_objects):
            prev_supply = steps[-1].want_supply if steps else cycle_iteration.principal
            prev_currency = steps[-1].want_currency if steps else cycle_iteration.currencies_order[0]

            conversion_result = self._converter.convert(
                have_currency=pair_obj.have_currency,
                want_currency=pair_obj.want_currency,
                have_amount=prev_supply
            )
            currency_gold_cost = self._gold_cost_manager.fetch_gold_cost(pair_obj.want_currency)
            total_gold_cost = currency_gold_cost * conversion_result.end_supply

            new_step = _CycleIterationStep(
                step_num=i + 1,
                have_currency=prev_currency,
                want_currency=pair_obj.want_currency,
                have_cost=prev_supply,
                want_supply=conversion_result.end_supply,
                average_ratio_used=conversion_result.average_ratio_used,
                gold_cost=total_gold_cost
            )
            steps.append(new_step)

        profit = steps[-1].want_supply - cycle_iteration.principal
        end_currency = steps[-1].want_currency

        if end_currency == Currency.DIVINE_ORB:
            divs_profit = profit
            to_div_conversion_ratio = ExchangeRatio(raw_ratio="1:1",
                                                    have_currency=Currency.DIVINE_ORB,
                                                    want_currency=Currency.DIVINE_ORB,
                                                    want_per_have=1)
        else:
            divs_conversion_result = self._converter.convert(have_currency=end_currency,
                                                             want_currency=Currency.DIVINE_ORB,
                                                             have_amount=profit)
            divs_profit = divs_conversion_result.end_supply
            to_div_conversion_ratio = divs_conversion_result.average_ratio_used

        iteration_result = _CycleIterationResult(divs_profit=divs_profit,
                                                 total_gold_cost=cycle_iteration.total_gold_cost,
                                                 to_div_ratio=to_div_conversion_ratio)
        cycle_iteration.result = iteration_result
        return divs_profit


def _create_cycle_rotations(cycle: list) -> list:
    return [cycle[i:] + cycle[:i] for i in range(len(cycle))]


class CurrencyArbitrager:

    def __init__(self,
                 market_data_manager: MarketDataManager,
                 gold_cost_manager: GoldCostManager):
        self._market_data_manager = market_data_manager

        self._cycle_stepper = _CycleIterationStepper(
            currency_converter=_CurrencyConverter(currency_pair_objects=self._market_data_manager.currency_pair_objs),
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

            if G.has_edge(pair_obj.have_currency, pair_obj.want_currency):
                raise RuntimeError(f"Edge {pair_obj.have_currency} -> {pair_obj.want_currency} already exists")

            G.add_edge(
                pair_obj.have_currency,
                pair_obj.want_currency,
                pair_obj=pair_obj
            )

        return G

    def _print_iterations(self, iterations: list[_CycleIteration]):
        sorted_iterations = sorted(iterations, key=lambda i: i.result.gold_per_div_profit)
        for i in sorted_iterations:
            print("\n\n")
            print(f"Gold per divines profit: {i.result.gold_per_div_profit}")
            print(f"{str(i)}")

    def arbitrage(self, valid_cycle_start_currencies: set[Currency] = None):
        self._verify_currency_pairs()

        G = self._create_graph()
        raw_cycles = nx.simple_cycles(G)
        all_raw_cycles = [rotated_cycle
                          for raw_cycle in raw_cycles
                          for rotated_cycle in _create_cycle_rotations(raw_cycle)]

        logger.info(f"\nStepping through arbitrage cycles...")
        processed_cycles = []
        for nodes in all_raw_cycles:
            cycle = _Cycle(nodes, graph=G)
            if valid_cycle_start_currencies and cycle.currency_pair_objects[0].have_currency not in valid_cycle_start_currencies:
                continue

            iterations = _CyclesIterationsFactory.create_cycle_iterations(cycle=cycle)
            cycle.iterations = iterations

            for iteration in iterations:
                self._cycle_stepper.step_through_cycle_iteration(cycle_iteration=iteration,
                                                                 currency_pair_objects=cycle.currency_pair_objects)

            processed_cycles.append(cycle)
        logger.info("\tFinished stepping through arbitrage cycles")

        all_iterations = [iteration for c in processed_cycles for iteration in c.iterations]
        profitable_iterations = [i for i in all_iterations if i.result.divs_profit > 0]
        self._print_iterations(profitable_iterations)

        return all_iterations
