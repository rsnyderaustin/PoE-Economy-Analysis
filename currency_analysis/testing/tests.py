import itertools
import logging
import random
from pathlib import Path

import cv2

from currency_analysis.arbitrage import CurrencyArbitrager
from currency_analysis.market_data_capture import (
    _MarketDataCaptureManager, _ScreenShotAnalyzer, MarketDataManager, _MarketSupplyTable, RatioType
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('testing')

def test_build_supply_table():
    # bounds = _ScreenBoundsCapturer(ui_element=_MarketUiElement.AVAILABLE_TRADES).capture()
    # table_screen_shot = _ScreenShotCapturer().capture(bounds=bounds)
    img_path = Path(__file__).resolve().parent / "available-trades.png"
    img_array = cv2.imread(str(img_path))
    supply_table = _ScreenShotAnalyzer(logger=logging.getLogger('testing')).analyze_for_table(
        img_array=img_array,
        have_currency='Divination Scarab of Pilfering',
        want_currency='Chaos Orb'
    )

def test_run():
    manager = _MarketDataCaptureManager(logger=logging.getLogger('testing'))
    manager.capture()

def test_fake_cycle():
    currencies = ['exalted orb', 'divine orb', 'chaos orb']
    market_data_manager = MarketDataManager(logger=logger)

    pairs = itertools.product(currencies, currencies)
    pairs = [p for p in pairs if p[0] != p[1]]
    for have_currency, want_currency in pairs:
        available_table = _MarketSupplyTable(ratio_type=RatioType.AVAILABLE,
                                             have_currency=have_currency,
                                             want_currency=want_currency)
        random_ratios = random.choices(range(25, 50), k=6)
        for ratio in random_ratios:
            available_table.add_ratio_supply(want_per_have=ratio,
                                             stock=random.choice(range(1, 20)))

        gold_cost = random.choice(range(250, 2000))
        want_currency_amount = random.choice(range(1, 10))

        market_data_manager.record_market_data(have_currency=have_currency,
                                               want_currency=want_currency,
                                               gold_cost=gold_cost,
                                               want_currency_amount=want_currency_amount,
                                               available_trades_table=available_table)

    arbitrager = CurrencyArbitrager(
        market_data_manager=market_data_manager,
        logger=logger
    )
    arbitrage_df = arbitrager.arbitrage()
    x=0

test_fake_cycle()
# test_run()
# test_build_supply_table()

