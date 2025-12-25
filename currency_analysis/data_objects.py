

import logging

logger = logging.getLogger(__name__)

import pandas as pd
from dataclasses import dataclass
from enum import Enum


class Currency(Enum):
    DIVINE_ORB = 'Divine Orb'
    CHAOS_ORB = 'Chaos Orb'
    VIVID_CRYSTALLISED_LIFEFORCE = 'Vivid Crystallised Lifeforce'
    STACKED_DECK = 'Stacked Deck'
    ORB_OF_ALCHEMY = 'Orb of Alchemy'
    ORB_OF_FUSING = 'Orb of Fusing'
    VAAL_ORB = 'Vaal Orb'
    ORB_OF_REGRET = 'Orb of Regret'
    REGAL_ORB = 'Regal Orb'
    ANCIENT_ORB = 'Ancient Orb'
    ORB_OF_SCOURING = 'Orb of Scouring'
    ORB_OF_ALTERATION = 'Orb of Alteration'
    ORB_OF_CHANCE = 'Orb of Chance'

class RatioType(Enum):
    AVAILABLE = 'available'
    COMPETING = 'competing'

@dataclass
class RatioSupply:
    raw_ratio: str
    ratio_type: RatioType
    have_currency: Currency
    want_currency: Currency
    want_per_have: float
    want_supply: int

    def to_dict(self):
        d = self.__dict__
        d['ratio_type'] = d['ratio_type'].value
        return d

    @classmethod
    def from_dict(cls, d: dict):
        d['ratio_type'] = RatioType(d['ratio_type'])
        return cls(**d)

    @property
    def buyout_cost(self) -> float:
        return (1 / self.want_per_have) * self.want_supply


class CurrencyPair:
    _max_rows = 6

    def __init__(self,
                 have_currency: Currency,
                 want_currency: Currency,
                 gold_cost_per_want: float = None,
                 ratios: list[RatioSupply] = None,
                 atts: dict = None):
        self.have_currency = have_currency
        self.want_currency = want_currency

        self._gold_cost_per_want = gold_cost_per_want

        self._ratios = ratios or []
        self._sorted_ratios = None

        self.atts = atts or dict()

    def to_dict(self) -> dict:
        d = self.__dict__.copy()
        d['_ratios'] = [r.to_dict() for r in self._ratios]
        return d

    @classmethod
    def from_dict(cls, d: dict):
        return cls(
            have_currency=d['have_currency'],
            want_currency=d['want_currency'],
            gold_cost_per_want=d.get('gold_cost_per_want'),
            ratios=[RatioSupply.from_dict(ratio_d) for ratio_d in d['ratios']],
            atts=d.get('atts', dict())
        )


    def determine_total_buyout_cost(self):
        """
        :return: The cost to buyout all posted ratios except for the very last
        """
        cls = self.__class__
        return sum(r.buyout_cost for r in self._ratios[:cls._max_rows - 1])

    def determine_total_buyout_supply(self):
        """
        :return: The total supply of all posted ratios except for the very last
        """
        cls = self.__class__
        return sum(r.supply for r in self._ratios[:cls._max_rows - 1])

    @property
    def sorted_ratios(self) -> list[RatioSupply]:
        if 'sorted_ratios' not in self.atts:
            self.atts['sorted_ratios'] = sorted(list(self._ratios), key=lambda r: r.want_per_have, reverse=True)

        return self.atts['sorted_ratios']

    def add_ratios(self, ratio_supplies: list[RatioSupply]):
        for ratio_supply in ratio_supplies:
            if ratio_supply.have_currency != self.have_currency:
                raise ValueError(f"Invalid have currency: {ratio_supply.have_currency}")

            if ratio_supply.want_currency != self.want_currency:
                raise ValueError(f"Invalid want currency: {ratio_supply.want_currency}")

            self._ratios.append(ratio_supply)

    def add_gold_cost(self, gold_cost: int, want_amount: int):
        self._gold_cost_per_want = gold_cost / want_amount




class MarketSupplyTable:

    def __init__(self,
                 ratio_type: RatioType,
                 have_currency: Currency,
                 want_currency: Currency):
        self.ratio_type = ratio_type
        self.have_currency = have_currency
        self.want_currency = want_currency

        self._ratios = dict()

    def print(self):
        ratio_rows = {
            'ratio': [],
            'want_per_have': [],
            'supply': []
        }
        for ratio in self._ratios.values():
            ratio_rows['ratio'].append(ratio.raw_ratio)
            ratio_rows['want_per_have'].append(ratio.want_per_have)
            ratio_rows['supply'].append(ratio.supply)
        df = pd.DataFrame(ratio_rows)
        print(f"Type: {self.ratio_type.value}\nHave: {self.have_currency}\tWant: {self.want_currency}")
        print(df)

    @property
    def supply_ratios(self) -> list[RatioSupply]:
        return list(self._ratios.values())

    def add_ratio_supply(self,
                         raw_ratio: str,
                         want_per_have: float,
                         want_supply: int):
        k = want_per_have, want_supply
        if k in self._ratios:
            r = self._ratios[k]
            r.want_per_have = r.want_per_have or want_per_have
            r.want_supply = r.supply or want_supply
        else:
            self._ratios[k] = RatioSupply(raw_ratio=raw_ratio,
                                          ratio_type=self.ratio_type,
                                          have_currency=self.have_currency,
                                          want_currency=self.want_currency,
                                          want_per_have=want_per_have,
                                          want_supply=want_supply)