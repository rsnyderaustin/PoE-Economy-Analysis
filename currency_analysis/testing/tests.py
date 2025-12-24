import itertools
import logging
import random
from pathlib import Path

import cv2

from currency_analysis.arbitrage import CurrencyArbitrager
from currency_analysis.cache import CacheSettings, CacheObject
from currency_analysis.market_data_capture import (
    MarketDataCaptureManager, _ScreenShotAnalyzer, MarketDataManager, _MarketSupplyTable, RatioType
)
from currency_analysis.ui_capture import UiBoundsCreator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('testing')

def test_build_supply_table():
    # bounds = _ScreenBoundsCapturer(ui_element=_MarketUiElement.AVAILABLE_TRADES).capture()
    # table_screen_shot = _ScreenShotCapturer().capture(bounds=bounds)
    img_path = Path(__file__).resolve().parent / "available-trades.png"
    img_array = cv2.imread(str(img_path))
    supply_table = _ScreenShotAnalyzer().extract_supply_table(
        img_array=img_array,
        have_currency='Divination Scarab of Pilfering',
        want_currency='Chaos Orb',
        ratio_type=RatioType.AVAILABLE
    )

def test_run():
    cache_settings = CacheSettings()
    cache_settings.add_settings(cache_objects=[CacheObject.MARKET_DATA_MANAGER],
                                load_from_cache=True,
                                save_to_cache=True)
    manager = MarketDataCaptureManager(cache_settings=cache_settings)
    manager.capture()

def test_fake_cycle():
    currencies = ['exalted orb', 'divine orb', 'chaos orb', 'transmutation orb', 'regal orb']
    market_data_manager = MarketDataManager()

    pairs = itertools.product(currencies, currencies)
    pairs = [p for p in pairs if p[0] != p[1]]
    for have_currency, want_currency in pairs:
        available_table = _MarketSupplyTable(ratio_type=RatioType.AVAILABLE,
                                             have_currency=have_currency,
                                             want_currency=want_currency)
        random_ratios = [random.uniform(0.05, 50) for _ in range(6)]
        for ratio in random_ratios:
            available_table.add_ratio_supply(raw_ratio='test',
                                             want_per_have=ratio,
                                             stock=random.choice(range(5, 100)))

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

def create_ui_bounds():
    creator = UiBoundsCreator()
    creator.create_bounds(show=True)

# test_fake_cycle()
# test_run()
# test_build_supply_table()
create_ui_bounds()

