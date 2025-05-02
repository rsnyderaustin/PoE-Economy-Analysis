
from enum import Enum
from typing import Any

from utils.enums import Currency


class MetaFilter:

    def __init__(self,
                 meta_filter_enum: Enum,
                 mod_value: Any,
                 price_currency_enum: Currency = None):
        """

        :param meta_filter_enum:
        :param mod_value: Should be a tuple if it represents a min and/or a max value (eg: 1 div minimum price should be (1,None)).
        :param price_currency_enum: This is only for filtering the price. 'Price' is an unusual filter because its dict
            includes a min/max (amount of currency) and an "option" (type of currency)
        """
        self.meta_filter_enum = meta_filter_enum
        self.mod_value = mod_value
        self.price_currency_enum = price_currency_enum


