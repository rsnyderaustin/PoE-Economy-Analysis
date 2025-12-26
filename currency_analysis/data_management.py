
import logging
logger = logging.getLogger(__name__)

from currency_analysis.data_objects import CurrencyPairMarketData, MarketSupplyTable, Currency, CurrencyPair


class MarketDataManager:

    def __init__(self,
                 currency_pairs: list[CurrencyPairMarketData] = None):
        self._pair_objs = {(p.have_currency, p.want_currency): p for p in currency_pairs} if currency_pairs else dict()

    @property
    def currency_pairs(self) -> list[CurrencyPair]:
        return [CurrencyPair(have_currency=p[0], want_currency=p[1]) for p in self._pair_objs.keys()]

    def to_dict(self) -> dict:
        return {'pair_objs': [p.to_dict() for k, p in self._pair_objs.items()]}

    @classmethod
    def from_dict(cls, d: dict) -> "MarketDataManager":
        pair_objs = [CurrencyPairMarketData.from_dict(pair_d) for pair_d in d['pair_objs']]
        return MarketDataManager(currency_pairs=pair_objs)


    def fetch_currency_pair_objs(self) -> list[CurrencyPairMarketData]:
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
            pair_obj.add_ratios(available_trades_table.supply_ratios)


class GoldCostManager:

    def __init__(self, gold_costs: dict = None):
        self._gold_costs = gold_costs or dict()

    def to_dict(self) -> dict:
        return {'gold_costs': self._gold_costs}

    @classmethod
    def from_dict(cls, d: dict) -> "GoldCostManager":
        return GoldCostManager(gold_costs=d['gold_costs'])

    def record_gold_cost(self,
                         want_currency: Currency,
                         want_supply: int,
                         gold_cost: int):
        if want_currency in self._gold_costs:
            logger.warning(f"{want_currency} already exists in self._gold_costs. Overwriting...")

        self._gold_costs[want_currency] = gold_cost / want_supply

    def fetch_gold_cost(self, want_currency: Currency):
        return self._gold_costs[want_currency]

    def need_to_record_gold_cost(self, want_currency: Currency):
        return want_currency not in self._gold_costs


class ImageCollectionsManager:

    def __init__(self):
        pass
