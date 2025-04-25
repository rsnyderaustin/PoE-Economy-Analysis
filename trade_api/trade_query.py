
from enum import Enum

from api_mediation import Price


class TradeQuery:

    filter_format = {

    }

    def __init__(self, league: str ="Standard"):
        self.league = league

    def create_trade_filter(self, price: Price):
