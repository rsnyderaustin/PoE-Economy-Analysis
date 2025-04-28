
from dataclasses import dataclass

from utils.enums import Currency


@dataclass
class Price:
    currency: Currency
    amount: int
