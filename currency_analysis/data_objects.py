

import logging
import math
from decimal import Decimal, ROUND_DOWN

logger = logging.getLogger(__name__)

import pandas as pd
from dataclasses import dataclass
from enum import Enum


class Currency(Enum):
    EXALTED_ORB = 'Exalted Orb'
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
    HARVEST_SCARAB_OF_DOUBLING = 'Harvest Scarab of Doubling'
    ULTIMATUM_SCARAB_OF_CATALYSING = 'Ultimatum Scarab of Catalysing'
    DIVINATION_SCARAB_OF_THE_CLOISTER = 'Divination Scarab of the Cloister'
    ENKINDLING_ORB = 'Enkindling Orb'
    CHROMATIC_ORB = 'Chromatic Orb'
    ORB_OF_ANNULMENT = 'Orb of Annulment'



class RatioType(Enum):
    AVAILABLE = 'available'
    COMPETING = 'competing'

@dataclass
class RatioSupply:
    raw_ratio: str
    have_currency: Currency
    want_currency: Currency
    want_per_have: float
    want_supply: int

    def __post_init__(self):
        if not isinstance(self.have_currency, Currency):
            raise TypeError(f"Invalid type for have_currency: {type(self.have_currency)}")

        if not isinstance(self.want_currency, Currency):
            raise TypeError(f"Invalid type for have_currency: {type(self.want_currency)}")

    def to_dict(self):
        d = self.__dict__.copy()
        d['have_currency'] = d['have_currency'].value
        d['want_currency'] = d['want_currency'].value
        return d

    @classmethod
    def from_dict(cls, d: dict):
        d['have_currency'] = Currency(d['have_currency'])
        d['want_currency'] = Currency(d['want_currency'])
        return cls(**d)

    @property
    def buyout_cost(self) -> float:
        return (1 / self.want_per_have) * self.want_supply

@dataclass(frozen=True)
class CurrencyPair:
    have_currency: Currency
    want_currency: Currency

class CurrencyPairMarketData:
    _max_rows = 6

    def __init__(self,
                 have_currency: Currency,
                 want_currency: Currency,
                 ratios: list[RatioSupply] = None,
                 atts: dict = None):
        self.have_currency = have_currency
        self.want_currency = want_currency

        self._ratios = ratios or []
        self._sorted_ratios = None

        self.atts = atts or dict()

    def to_dict(self) -> dict:
        d = self.__dict__.copy()
        d['have_currency'] = d['have_currency'].value
        d['want_currency'] = d['want_currency'].value
        d['_ratios'] = [r.to_dict() for r in self._ratios]
        return d

    @classmethod
    def from_dict(cls, d: dict):
        return cls(
            have_currency=Currency(d['have_currency']),
            want_currency=Currency(d['want_currency']),
            ratios=[RatioSupply.from_dict(ratio_d) for ratio_d in d['_ratios']],
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

class MarketSupplyTable:

    def __init__(self,
                 have_currency: Currency,
                 want_currency: Currency):
        self.have_currency = have_currency
        self.want_currency = want_currency

        self.supply_ratios = []

    def print(self):
        ratio_rows = {
            'ratio': [],
            'want_per_have': [],
            'supply': []
        }
        for ratio in self.supply_ratios:
            ratio_rows['ratio'].append(ratio.raw_ratio)
            ratio_rows['want_per_have'].append(ratio.want_per_have)
            ratio_rows['supply'].append(ratio.want_supply)
        df = pd.DataFrame(ratio_rows)
        print(f"Have: {self.have_currency}\tWant: {self.want_currency}")
        print(df)

    def add_ratio_supply(self,
                         raw_ratio: str,
                         want_per_have: float,
                         want_supply: int,
                         check_for_ratio_imbalance: bool = True):
        if self.supply_ratios and check_for_ratio_imbalance:
            current_ratios = [r.want_per_have for r in self.supply_ratios]

            portion_from_range = min(
                want_per_have / min(current_ratios),
                want_per_have / max(current_ratios)
            )
            if portion_from_range < 0.2 or portion_from_range > 5.0:
                print(f"\n\nFound significant difference in ratios:"
                      f"\n\tPassed ratio {want_per_have}"
                      f"\n\tPrevious ratios: {current_ratios}")
                i = input("Select an option:"
                      "\n\t1: Change the passed ratio"
                      "\n\t2: Change the previous ratios"
                      "\n\t3: No changes")
                i = int(i.replace(' ', ''))
                if i == 1:
                    want_per_have = float(input("Enter the new ratio here:"))
                elif i == 2:
                    for ratio_obj in self.supply_ratios:
                        new_ratio = input(f"Enter new ratio to replace {ratio_obj.want_per_have}:")
                        new_ratio = float(new_ratio)
                        ratio_obj.want_per_have = new_ratio
                elif i == 3:
                    pass
                else:
                    raise ValueError("Invalid option")

        self.supply_ratios.append(RatioSupply(raw_ratio=raw_ratio,
                                              have_currency=self.have_currency,
                                              want_currency=self.want_currency,
                                              want_per_have=want_per_have,
                                              want_supply=want_supply))