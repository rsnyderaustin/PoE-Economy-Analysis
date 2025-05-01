
import logging

from external_apis import TradeApiCoordinator

logging.basicConfig(level=logging.INFO,
                    force=True)

trade_api_coord = TradeApiCoordinator()
trade_api_coord.fill_internal_data()
x=0
