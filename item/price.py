
from dataclasses import dataclass

from utils import Currency


@dataclass
class Price:
    currency: Currency
    amount: int
