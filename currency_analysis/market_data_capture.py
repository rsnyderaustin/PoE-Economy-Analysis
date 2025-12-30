import itertools
import logging
from dataclasses import dataclass
from typing import Iterable

from currency_analysis import utils
from currency_analysis.data_management import MarketDataManager, GoldCostManager, ImageCollectionsManager
from currency_analysis.data_objects import RatioType, Currency

logger = logging.getLogger(__name__)

from currency_analysis.cache import (CacheObject, CacheSettings, MarketDataManagerCache,
                                     GoldCostManagerCache, MarketDataImagesCache)
from currency_analysis.ui_capture import ScreenShotsCoordinator, UiBoundsCreator, MarketImageCollection
from currency_analysis.visual_analysis import ScreenShotAnalyzer


@dataclass
class RequiredCurrencyData:
    currency_gold_costs: set[Currency]
    currency_pair_market_data: set[tuple[Currency, Currency]]

class RequiredDataDeterminer:

    @classmethod
    def _create_currency_pairs(cls, currencies: set[Currency]) -> set[frozenset[Currency]]:
        return {frozenset(pair) for pair in itertools.combinations(currencies, 2)
                if pair[0] != pair[1]}

    @classmethod
    def determine_required_data(cls,
                                currencies_to_record: set[Currency],
                                gold_cost_manager: GoldCostManager,
                                market_data_manager: MarketDataManager) -> RequiredCurrencyData:
        record_market_currency_pairs = cls._create_currency_pairs(currencies_to_record)

        existing_market_currency_pairs = {frozenset({p.have_currency, p.want_currency})
                                          for p in market_data_manager.currency_pairs}
        unique_market_currency_pairs = record_market_currency_pairs - existing_market_currency_pairs
        unique_market_currency_pairs = {tuple(p) for p in unique_market_currency_pairs}

        record_gold_cost_currencies = {c for c in currencies_to_record if gold_cost_manager.need_to_record_gold_cost(c)}

        return RequiredCurrencyData(
            currency_gold_costs=record_gold_cost_currencies,
            currency_pair_market_data=unique_market_currency_pairs
        )


class MarketDataCaptureManager:

    def __init__(self,
                 cache_settings: CacheSettings):
        self._cache_settings = cache_settings

        self._market_data_manager_cache = MarketDataManagerCache()
        if cache_settings.should_load_from_cache(CacheObject.MARKET_DATA_MANAGER):
            self.market_data_manager = self._create_manager_from_cache(
                cache=self._market_data_manager_cache,
                cache_object=CacheObject.MARKET_DATA_MANAGER,
                manager_cls=MarketDataManager
            )
        else:
            self.market_data_manager = MarketDataManager()

        self._gold_cost_manager_cache = GoldCostManagerCache()
        if cache_settings.should_load_from_cache(CacheObject.GOLD_COST_MANAGER):
            self.gold_cost_manager = self._create_manager_from_cache(
                cache=self._gold_cost_manager_cache,
                cache_object=CacheObject.GOLD_COST_MANAGER,
                manager_cls=GoldCostManager
            )
        else:
            self.gold_cost_manager = GoldCostManager()

    def _create_manager_from_cache(self, cache, cache_object: CacheObject, manager_cls):
        manager = None
        if self._cache_settings.should_load_from_cache(cache_object):
            manager = cache.load(
                missing_ok=self._cache_settings.missing_ok(cache_object)
            )

        if not manager:
            manager = manager_cls()

        return manager

    def _process_market_image_collections(self, market_image_collections: Iterable[MarketImageCollection]):
        for i, collection in enumerate(market_image_collections):
            logger.info(f"Processing MarketImageCollection {i} of {len(market_image_collections)}")
            available_table = ScreenShotAnalyzer.extract_supply_table(
                ratio_img_arrays=[currency_ui_row.ratio_img.img_array
                                  for currency_ui_row in collection.available_currency_ui_rows],
                stock_img_arrays=[currency_ui_row.stock_img.img_array
                                  for currency_ui_row in collection.available_currency_ui_rows],
                ratio_type=RatioType.AVAILABLE,
                have_currency=collection.have_currency,
                want_currency=collection.want_currency,
                rows_to_extract=3
            ) if collection.available_currency_ui_rows else None
            self.market_data_manager.record_market_data(
                want_currency=collection.want_currency,
                have_currency=collection.have_currency,
                available_trades_table=available_table
            )

            """
            ScreenShotAnalyzer.extract_supply_table() properly handles reversing the competing table for us,
            so we feed it the correct have and want Currencies. But then we do have to flip it for
            record_market_data()
            """
            competing_table = ScreenShotAnalyzer.extract_supply_table(
                ratio_img_arrays=[currency_ui_row.ratio_img.img_array
                                  for currency_ui_row in collection.competing_currency_ui_rows],
                stock_img_arrays=[currency_ui_row.stock_img.img_array
                                  for currency_ui_row in collection.competing_currency_ui_rows],
                ratio_type=RatioType.COMPETING,
                have_currency=collection.have_currency,
                want_currency=collection.want_currency,
                rows_to_extract=3
            ) if collection.competing_currency_ui_rows else None
            self.market_data_manager.record_market_data(
                want_currency=collection.have_currency,
                have_currency=collection.want_currency,
                available_trades_table=competing_table
            )

        if self._cache_settings.should_save_to_cache(cache_object=CacheObject.MARKET_DATA_MANAGER):
            self._market_data_manager_cache.save(self.market_data_manager)

    def _capture_gold_cost(self, currency: Currency):
        gold_cost = utils.capture_user_input(prompt=f"Enter gold cost per currency for {currency.value}: ",
                                             convert_to=float)
        self.gold_cost_manager.add_gold_cost(currency=currency,
                                             gold_cost_per_currency=gold_cost)

        if self._cache_settings.should_save_to_cache(CacheObject.GOLD_COST_MANAGER):
            self._gold_cost_manager_cache.save(self.gold_cost_manager)


    def capture(self, currencies: set[Currency]):
        if self._cache_settings.should_load_from_cache(CacheObject.IMAGE_COLLECTIONS_MANAGER):
            image_collections_manager = self._create_manager_from_cache(
                cache=MarketDataImagesCache(),
                cache_object=CacheObject.IMAGE_COLLECTIONS_MANAGER,
                manager_cls=ImageCollectionsManager
            )
            self._process_market_images(image_collections_manager.image_collections)

        required_data = RequiredDataDeterminer.determine_required_data(
            currencies_to_record=currencies,
            gold_cost_manager=self.gold_cost_manager,
            market_data_manager=self.market_data_manager
        )
        gold_costs_to_record = required_data.currency_gold_costs

        if not required_data.currency_gold_costs and not required_data.currency_pair_market_data:
            return

        bounds_manager = UiBoundsCreator.create_bounds(show=False)
        screen_shot_coordinator = ScreenShotsCoordinator(screen_bounds_manager=bounds_manager)
        for market_data_image_collection in screen_shot_coordinator.capture_screen_shots(
            currency_pairs_to_capture=set(required_data.currency_pair_market_data),
            show=False
        ):
            if market_data_image_collection.have_currency in gold_costs_to_record:
                self._capture_gold_cost(market_data_image_collection.have_currency)
                gold_costs_to_record.remove(market_data_image_collection.have_currency)

            if market_data_image_collection.want_currency in gold_costs_to_record:
                self._capture_gold_cost(market_data_image_collection.want_currency)
                gold_costs_to_record.remove(market_data_image_collection.want_currency)

            self._process_market_image_collections(market_image_collections=[market_data_image_collection])
