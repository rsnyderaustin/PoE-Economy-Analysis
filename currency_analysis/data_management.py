from currency_analysis.data_objects import CurrencyPair, MarketSupplyTable, Currency


class MarketDataManager:

    def __init__(self,
                 currency_pairs: list[CurrencyPair] = None):
        self._pair_objs = {(p.have_currency, p.want_currency): p for p in currency_pairs} if currency_pairs else dict()

    def to_dict(self) -> dict:
        return {'pair_objs': [p.to_dict() for k, p in self._pair_objs.items()]}

    @classmethod
    def from_dict(cls, d: dict) -> "MarketDataManager":
        pair_objs = [CurrencyPair.from_dict(pair_d) for pair_d in d['pair_objs']]
        return MarketDataManager(currency_pairs=pair_objs)


    def fetch_currency_pair_objs(self) -> list[CurrencyPair]:
        return list(self._pair_objs.values())

    def record_market_data(self,
                           want_currency: Currency,
                           have_currency: Currency,
                           gold_cost: int = None,
                           want_currency_amount: int = None,
                           available_trades_table: MarketSupplyTable | None = None,
                           competing_trades_table: MarketSupplyTable | None = None):
        k = have_currency, want_currency
        if k not in self._pair_objs:
            self._pair_objs[k] = CurrencyPair(have_currency=have_currency,
                                              want_currency=want_currency)
        pair_obj = self._pair_objs[k]

        if available_trades_table:
            pair_obj.add_ratios(available_trades_table.supply_ratios)

        if competing_trades_table:
            pair_obj.add_ratios(competing_trades_table.supply_ratios)

        if gold_cost and want_currency_amount:
            pair_obj.add_gold_cost(gold_cost=gold_cost,
                                   want_amount=want_currency_amount)