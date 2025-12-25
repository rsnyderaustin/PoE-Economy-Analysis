import logging
from typing import Iterable

from currency_analysis.data_management import MarketDataManager
from currency_analysis.data_objects import RatioType

logger = logging.getLogger(__name__)

import string

from currency_analysis.cache import CacheObject, CacheSettings, MarketDataImageCache, MarketDataManagerCache
from currency_analysis.ui_capture import UiElement, ScreenShotsCoordinator, UiImageCollection, UiBoundsCreator
from currency_analysis.visual_analysis import ScreenShotAnalyzer


class MarketDataCaptureManager:

    def __init__(self,
                 cache_settings: CacheSettings):
        self._cache_settings = cache_settings

        self._market_data_manager_cache = MarketDataManagerCache()
        self._market_data_manager = self._create_market_data_manager(self._market_data_manager_cache)

        self._image_cache = MarketDataImageCache()
        self._screen_shot_analyzer = ScreenShotAnalyzer()
        self._market_data_manager = MarketDataManager()

    def _record_market_data(
            self,
            ui_image_collection: UiImageCollection
    ):
        print("Recording market data...")
        a = self._screen_shot_analyzer
        c = ui_image_collection

        currency_allowed_chars = f"{string.ascii_letters} "
        # --- Required fields ---
        print("\tExtracting Want Currency string...")
        want_currency_strings = a.extract_strings(
            img_array=c.fetch_images(ui_element=UiElement.WANT_CURRENCY)[0].img_array,
            allowed_chars=currency_allowed_chars
        )
        want_currency = ''.join(want_currency_strings)

        print("\tExtracting Have Currency string...")
        have_currency_strings = a.extract_strings(
            img_array=c.fetch_images(ui_element=UiElement.HAVE_CURRENCY)[0].img_array,
            allowed_chars=currency_allowed_chars
        )
        have_currency = ''.join(have_currency_strings)

        if c.has_images(UiElement.WANT_CURRENCY_AMOUNT):
            print("\tExtracting Want Currency Amount string...")
            want_currency_amount_strings = a.extract_strings(
                img_array=c.fetch_images(ui_element=UiElement.WANT_CURRENCY_AMOUNT)[0].img_array,
                allowed_chars='1234567890',
                white_threshold=100
            )
            want_currency_amount = int(''.join(want_currency_amount_strings))
        else:
            want_currency_amount = None

        if c.has_images(UiElement.GOLD_COST):
            print("\tExtracting Gold Cost string...")
            gold_cost_strings = a.extract_strings(
                img_array=c.fetch_images(ui_element=UiElement.GOLD_COST)[0].img_array,
                allowed_chars='1234567890,'
            )
            if len(gold_cost_strings) == 1:
                gold_cost_str = gold_cost_strings[0]
            elif len(gold_cost_strings) == 2:
                gold_cost_str = gold_cost_strings[1]
            else:
                raise ValueError(f"Invalid gold cost strings: {gold_cost_strings}")

            gold_cost_str = gold_cost_str.replace(',', '')
            gold_cost = int(gold_cost_str)
        else:
            gold_cost = None

        if c.has_images(UiElement.AVAILABLE_TRADES):
            print("\tExtracting Available Trades table...")
            available_trades_table = self._screen_shot_analyzer.extract_supply_table(
                img_arrays=[i.img_array for i in c.fetch_images(ui_element=UiElement.AVAILABLE_TRADES)],
                ratio_type=RatioType.AVAILABLE,
                have_currency=have_currency,
                want_currency=want_currency
            )
        else:
            available_trades_table = None

        if c.has_images(UiElement.COMPETING_TRADES):
            print("\tExtracting Competing Trades table")
            competing_trades_table = self._screen_shot_analyzer.extract_supply_table(
                img_arrays=[i.img_array for i in c.fetch_images(ui_element=UiElement.COMPETING_TRADES)],
                ratio_type=RatioType.AVAILABLE,
                have_currency=have_currency,
                want_currency=want_currency
            )
        else:
            competing_trades_table = None

        self._market_data_manager.record_market_data(
            want_currency=want_currency,
            have_currency=have_currency,
            want_currency_amount=want_currency_amount,
            gold_cost=gold_cost,
            available_trades_table=available_trades_table,
            competing_trades_table=competing_trades_table
        )
        print("\tFinished recording market data.")
        
    def _create_market_data_manager(self, cache: MarketDataManagerCache) -> MarketDataManager:
        market_data_manager = None
        if self._cache_settings.should_load_from_cache(CacheObject.MARKET_DATA_MANAGER):
            market_data_manager = cache.load(missing_ok=self._cache_settings.missing_ok(CacheObject.MARKET_DATA_MANAGER))

        if not market_data_manager:
            market_data_manager = MarketDataManager()
        
        return market_data_manager

    def _create_ui_image_collections(self) -> Iterable[UiImageCollection]:
        screen_shot_collections = None
        if self._cache_settings.should_load_from_cache(CacheObject.UI_IMAGE_COLLECTION):
            screen_shot_collections = self._image_cache.load(
                missing_ok=self._cache_settings.missing_ok(CacheObject.UI_IMAGE_COLLECTION)
            )

        if not screen_shot_collections:
            bounds_manager = UiBoundsCreator.create_bounds(show=False)
            screen_shot_coordinator = ScreenShotsCoordinator(screen_bounds_manager=bounds_manager)
            screen_shot_collections = screen_shot_coordinator.capture_screen_shots()

        return screen_shot_collections

    def capture(self) -> MarketDataManager:
        ui_image_collections = self._create_ui_image_collections()

        for ui_image_collection in ui_image_collections:
            if self._cache_settings.should_save_to_cache(CacheObject.UI_IMAGE_COLLECTION):
                self._image_cache.save(ui_image_collection)

            self._record_market_data(ui_image_collection=ui_image_collection)

            if self._cache_settings.should_save_to_cache(CacheObject.MARKET_DATA_MANAGER):
                self._market_data_manager_cache.save(self._market_data_manager)

        return self._market_data_manager
