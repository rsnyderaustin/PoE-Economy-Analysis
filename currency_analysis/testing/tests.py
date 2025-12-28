import logging
import random
from pathlib import Path

import cv2

from currency_analysis.arbitrage import CurrencyArbitrager
from currency_analysis.cache import CacheSettings, CacheObject
from currency_analysis.data_management import GoldCostManager
from currency_analysis.data_objects import RatioType, MarketSupplyTable, Currency
from currency_analysis.market_data_capture import MarketDataCaptureManager, MarketDataManager, RequiredDataDeterminer
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

    currencies = {Currency.STACKED_DECK,
                  Currency.CHAOS_ORB,
                  Currency.DIVINE_ORB,
                  Currency.CHROMATIC_ORB,
                  Currency.VIVID_CRYSTALLISED_LIFEFORCE,
                  Currency.ORB_OF_SCOURING}

    cache_settings = CacheSettings()
    cache_settings.add_settings(cache_objects=[CacheObject.GOLD_COST_MANAGER],
                                load_from_cache=True,
                                save_to_cache=True,
                                missing_ok=False)
    cache_settings.add_settings(cache_objects=[CacheObject.MARKET_DATA_MANAGER],
                                load_from_cache=True,
                                save_to_cache=True,
                                missing_ok=True)
    cache_settings.add_settings(cache_objects=[CacheObject.IMAGE_COLLECTIONS_MANAGER],
                                load_from_cache=False,
                                save_to_cache=False,
                                missing_ok=True)
    manager = MarketDataCaptureManager(cache_settings=cache_settings)
    manager.capture(currencies)

    arbitrager = CurrencyArbitrager(
        market_data_manager=manager.market_data_manager,
        gold_cost_manager=manager.gold_cost_manager
    )
    arbitrage_df = arbitrager.arbitrage()
    x = 0

def test_arbitrage():
    cache_settings = CacheSettings()
    cache_settings.add_settings(cache_objects=[CacheObject.GOLD_COST_MANAGER],
                                load_from_cache=True,
                                save_to_cache=False,
                                missing_ok=False)
    cache_settings.add_settings(cache_objects=[CacheObject.MARKET_DATA_MANAGER],
                                load_from_cache=True,
                                save_to_cache=False,
                                missing_ok=True)
    cache_settings.add_settings(cache_objects=[CacheObject.IMAGE_COLLECTIONS_MANAGER],
                                load_from_cache=False,
                                save_to_cache=False,
                                missing_ok=True)
    manager = MarketDataCaptureManager(cache_settings=cache_settings)

    arbitrager = CurrencyArbitrager(
        market_data_manager=manager.market_data_manager,
        gold_cost_manager=manager.gold_cost_manager
    )
    arbitrage_df = arbitrager.arbitrage()
    arbitrage_profit_df = arbitrage_df[arbitrage_df['divs_profit'] > 0]
    x=0


def _create_randomized_tables(have_currency: Currency,
                              want_currency: Currency) -> tuple[MarketSupplyTable, MarketSupplyTable]:
    table = MarketSupplyTable(have_currency=have_currency,
                              want_currency=want_currency)
    ratio_start = random.uniform(0.001, 1000)
    table.add_ratio_supply(raw_ratio='test',
                           want_per_have=ratio_start,
                           want_supply=random.choice(range(5, 10000)),
                           check_for_ratio_imbalance=False)
    for i in range(5):
        new_ratio = ratio_start + (ratio_start * i)
        table.add_ratio_supply(raw_ratio='test',
                               want_per_have=new_ratio,
                               want_supply=random.choice(range(5, 10000)),
                               check_for_ratio_imbalance=False)

    reverse_table = MarketSupplyTable(have_currency=want_currency,
                                      want_currency=have_currency)
    r_ratio_start = 1 / ratio_start
    reverse_table.add_ratio_supply(raw_ratio='test',
                                   want_per_have=r_ratio_start,
                                   want_supply=random.choice(range(5, 10000)),
                                   check_for_ratio_imbalance=False)
    for i in range(5):
        new_ratio = r_ratio_start + (r_ratio_start + (r_ratio_start * i * 0.05))
        reverse_table.add_ratio_supply(raw_ratio='test',
                                       want_per_have=new_ratio,
                                       want_supply=random.choice(range(5, 10000)),
                                       check_for_ratio_imbalance=False)

    return table, reverse_table

def test_fake_cycle():
    currencies = [Currency.EXALTED_ORB,
                  Currency.DIVINE_ORB,
                  Currency.CHAOS_ORB,
                  Currency.REGAL_ORB,
                  Currency.ORB_OF_SCOURING]
    currency_pairs = RequiredDataDeterminer._create_currency_pairs(set(currencies))

    market_data_manager = MarketDataManager()
    gold_cost_manager = GoldCostManager()
    for have_currency, want_currency in currency_pairs:
        gold_cost_manager.add_gold_cost(
            currency=want_currency,
            want_supply=1,
            gold_cost=random.choice(range(50, 250))
        )
        gold_cost_manager.add_gold_cost(
            currency=have_currency,
            want_supply=1,
            gold_cost=random.choice(range(50, 250))
        )
        available_table, reverse_table = _create_randomized_tables(have_currency=have_currency,
                                                                   want_currency=want_currency)
        market_data_manager.record_market_data(have_currency=have_currency,
                                               want_currency=want_currency,
                                               available_trades_table=available_table)
        market_data_manager.record_market_data(have_currency=want_currency,
                                               want_currency=have_currency,
                                               available_trades_table=reverse_table)

        gold_cost_manager.add_gold_cost(currency=want_currency,
                                        gold_cost=random.choice(range(250, 2000)),
                                        want_supply=random.choice(range(1, 10)))
        gold_cost_manager.add_gold_cost(currency=have_currency,
                                        gold_cost=random.choice(range(250, 2000)),
                                        want_supply=random.choice(range(1, 10)))

    arbitrager = CurrencyArbitrager(
        market_data_manager=market_data_manager,
        gold_cost_manager=gold_cost_manager
    )
    arbitrage_df = arbitrager.arbitrage()
    x=0

def create_ui_bounds():
    creator = UiBoundsCreator()
    creator.create_bounds(show=True)

def _same_graph(G1, G2):
    if set(G1.nodes) != set(G2.nodes):
        return False

    if set(G1.edges) != set(G2.edges):
        return False

    for u, v in G1.edges:
        if G1[u][v] != G2[u][v]:
            return False

    return True

def _arbitrage_df_to_tuples(arbitrage_df):
    rows = set(arbitrage_df[[
        'iteration_principal',
        'step_num',
        'have',
        'want',
        'have_cost',
        'want_supply'
    ]].itertuples(index=False, name=None))
    return rows

def _determine_best_cycles(df, k: int):
    top_ids = (
        df['cycle_iteration_id']
        .drop_duplicates()
        .head(k)
    )

    top_cycles = df[df['cycle_iteration_id'].isin(top_ids)]

    return top_cycles


def test_graph_creation():
    cache_settings = CacheSettings()
    cache_settings.add_settings(cache_objects=[CacheObject.GOLD_COST_MANAGER],
                                load_from_cache=True,
                                save_to_cache=False,
                                missing_ok=False)
    cache_settings.add_settings(cache_objects=[CacheObject.MARKET_DATA_MANAGER],
                                load_from_cache=True,
                                save_to_cache=False,
                                missing_ok=True)
    cache_settings.add_settings(cache_objects=[CacheObject.IMAGE_COLLECTIONS_MANAGER],
                                load_from_cache=False,
                                save_to_cache=False,
                                missing_ok=True)
    manager = MarketDataCaptureManager(cache_settings=cache_settings)

    arbitrager1 = CurrencyArbitrager(
        market_data_manager=manager.market_data_manager,
        gold_cost_manager=manager.gold_cost_manager
    )
    arbitrager2 = CurrencyArbitrager(
        market_data_manager=manager.market_data_manager,
        gold_cost_manager=manager.gold_cost_manager
    )
    g1 = arbitrager1._create_graph()
    g2 = arbitrager2._create_graph()
    same = _same_graph(g1, g2)

    arbitrage_df1 = arbitrager1.arbitrage()
    arbitrage_df2 = arbitrager2.arbitrage()

    tuples1 = _arbitrage_df_to_tuples(arbitrage_df1)
    tuples2 = _arbitrage_df_to_tuples(arbitrage_df2)
    missing_tuples = tuples1 - tuples2

    arbitrage_profit_df1 = arbitrage_df1[arbitrage_df1['divs_profit'] > 0]
    arbitrage_profit_df2 = arbitrage_df2[arbitrage_df2['divs_profit'] > 0]

    top_ids1 = (
        arbitrage_profit_df1['cycle_iteration_id']
        .drop_duplicates()
        .head(3)
    )

    best_cycles1 = _determine_best_cycles(df=arbitrage_profit_df1, k=3)
    best_cycles2 = _determine_best_cycles(df=arbitrage_profit_df2, k=3)

    x=0

# test_fake_cycle()
# test_run()
# test_arbitrage()
# test_build_supply_table()
# create_ui_bounds()
test_graph_creation()

