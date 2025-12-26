import logging
import random
from pathlib import Path

import cv2

from currency_analysis.arbitrage import CurrencyArbitrager
from currency_analysis.cache import CacheSettings, CacheObject
from currency_analysis.data_objects import RatioType, MarketSupplyTable, Currency
from currency_analysis.market_data_capture import MarketDataCaptureManager, MarketDataManager
from currency_analysis.ui_capture import UiBoundsCreator
from currency_analysis.visual_analysis import ScreenShotAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('testing')

def test_build_supply_table():
    # bounds = _ScreenBoundsCapturer(ui_element=_MarketUiElement.AVAILABLE_TRADES).capture()
    # table_screen_shot = _ScreenShotCapturer().capture(bounds=bounds)
    img_path = Path(__file__).resolve().parent / "available-trades.png"
    img_array = cv2.imread(str(img_path))
    supply_table = ScreenShotAnalyzer().extract_supply_table(
        img_arrays=[img_array],
        have_currency='Divination Scarab of Pilfering',
        want_currency='Chaos Orb',
        ratio_type=RatioType.AVAILABLE
    )

def test_run():
    currencies = {Currency.EXALTED_ORB,
                  Currency.DIVINE_ORB,
                  Currency.CHAOS_ORB,
                  Currency.DIVINATION_SCARAB_OF_THE_CLOISTER,
                  Currency.HARVEST_SCARAB_OF_DOUBLING,
                  Currency.ULTIMATUM_SCARAB_OF_CATALYSING,
                  Currency.ORB_OF_SCOURING}

    cache_settings = CacheSettings()
    cache_settings.add_settings(cache_objects=[CacheObject.MARKET_DATA_MANAGER,
                                               CacheObject.IMAGE_COLLECTIONS_MANAGER,
                                               CacheObject.GOLD_COST_MANAGER],
                                load_from_cache=False,
                                save_to_cache=True,
                                missing_ok=True)
    manager = MarketDataCaptureManager(cache_settings=cache_settings)
    manager.capture(currencies)

def test_fake_cycle():
    currencies = [Currency.EXALTED_ORB,
                  Currency.DIVINE_ORB,
                  Currency.CHAOS_ORB,
                  Currency.REGAL_ORB,
                  Currency.ORB_OF_SCOURING]
    pairs = []
    market_data_manager = MarketDataManager()
    for have_currency, want_currency in pairs:
        available_table = MarketSupplyTable(ratio_type=RatioType.AVAILABLE,
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
test_run()
# test_build_supply_table()
# create_ui_bounds()

