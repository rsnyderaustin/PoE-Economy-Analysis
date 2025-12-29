
import logging

from currency_analysis.data_objects import CurrencyPairMarketData, MarketSupplyTable, Currency, CurrencyPair


logger = logging.getLogger(__name__)


class MarketDataManager:

    def __init__(self,
                 currency_pairs: list[CurrencyPairMarketData] = None):
        self._pair_objs = self._create_pair_objects_dict(currency_pairs) if currency_pairs else dict()

    def _create_pair_objects_dict(self, pair_objects: list[CurrencyPairMarketData]) -> dict:
        d = dict()
        for po in pair_objects:
            k = po.have_currency, po.want_currency
            if k in d:
                raise ValueError(f"Duplicate entry for MarketDataManager CurrencyPairMarketData dictionary."
                                 f"\n\tHave: {po.have_currency}"
                                 f"\n\tWant: {po.want_currency}")
            d[k] = po
        return d

    @property
    def currency_pairs(self) -> list[CurrencyPair]:
        return [CurrencyPair(have_currency=p[0], want_currency=p[1]) for p in self._pair_objs.keys()]

    def to_dict(self) -> dict:
        return {'pair_objs': [p.to_dict() for k, p in self._pair_objs.items()]}

    @classmethod
    def from_dict(cls, d: dict) -> "MarketDataManager":
        pair_objs = [CurrencyPairMarketData.from_dict(pair_d) for pair_d in d['pair_objs']]
        return MarketDataManager(currency_pairs=pair_objs)

    @property
    def currency_pair_objs(self) -> list[CurrencyPairMarketData]:
        return list(self._pair_objs.values())

    def record_market_data(self,
                           want_currency: Currency,
                           have_currency: Currency,
                           available_trades_table: MarketSupplyTable | None = None):
        k = have_currency, want_currency
        if k not in self._pair_objs:
            self._pair_objs[k] = CurrencyPairMarketData(have_currency=have_currency,
                                                        want_currency=want_currency)
        pair_obj = self._pair_objs[k]

        if available_trades_table:
            pair_obj.add_ratios(available_trades_table.ratio_supplies)


class GoldCostManager:

    def __init__(self, gold_costs: dict = None):
        self._gold_costs = gold_costs or dict()

    def to_dict(self) -> dict:
        d = self._gold_costs.copy()
        return {'gold_costs': {c_enum.value: v for c_enum, v in d.items()}}

    @classmethod
    def from_dict(cls, d: dict) -> "GoldCostManager":
        d = {Currency(k): v for k, v in d['gold_costs'].items()}
        return GoldCostManager(gold_costs=d)

    def add_gold_cost(self,
                      currency: Currency,
                      gold_cost_per_currency: float):
        if currency in self._gold_costs:
            logger.warning(f"{currency} already exists in self._gold_costs. Overwriting...")

        self._gold_costs[currency] = gold_cost_per_currency

    def fetch_gold_cost(self, want_currency: Currency):
        return self._gold_costs[want_currency]

    def need_to_record_gold_cost(self, want_currency: Currency):
        return want_currency not in self._gold_costs


class ImageCollectionsManager:

    def __init__(self):
        pass
