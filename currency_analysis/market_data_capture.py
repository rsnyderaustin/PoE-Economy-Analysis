import itertools
import logging
from dataclasses import dataclass
from typing import Iterable

from currency_analysis.data_management import MarketDataManager, GoldCostManager, ImageCollectionsManager
from currency_analysis.data_objects import RatioType, Currency

logger = logging.getLogger(__name__)

from currency_analysis.cache import (CacheObject, CacheSettings, MarketDataManagerCache,
    GoldCostManagerCache, ImageCollectionsManagerCache)
from currency_analysis.ui_capture import (ScreenShotsCoordinator, ImageCollection, UiBoundsCreator,
    MarketDataImages, GoldCostImages)
from currency_analysis.visual_analysis import ScreenShotAnalyzer


@dataclass
class RequiredCurrencyData:
    currency_gold_costs: Iterable[Currency]
    currency_pair_market_data: Iterable[tuple[Currency, Currency]]

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

    def _process_image_collections(self, image_collections: Iterable[ImageCollection]):
        for collection in image_collections:
            if isinstance(collection, MarketDataImages):
                available_table = ScreenShotAnalyzer.extract_supply_table(
                    img_arrays=[img.img_array for img in collection.available_currency_images],
                    ratio_type=RatioType.AVAILABLE,
                    have_currency=collection.have_currency,
                    want_currency=collection.want_currency
                ) if collection.available_currency_images else None
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
                    img_arrays=[img.img_array for img in collection.competing_currency_images],
                    ratio_type=RatioType.COMPETING,
                    have_currency=collection.have_currency,
                    want_currency=collection.want_currency
                ) if collection.competing_currency_images else None
                self.market_data_manager.record_market_data(
                    want_currency=collection.have_currency,
                    have_currency=collection.want_currency,
                    available_trades_table=competing_table
                )
            elif isinstance(collection, GoldCostImages):
                gold_cost = ScreenShotAnalyzer.extract_number(
                    img_array=collection.gold_cost_image.img_array,
                    num_type=int,
                    white_threshold=100
                )
                currency_amount = ScreenShotAnalyzer.extract_number(
                    img_array=collection.currency_amount_image.img_array,
                    num_type=int
                )

                self.gold_cost_manager.add_gold_cost(gold_cost=gold_cost,
                                                     want_currency=collection.currency,
                                                     want_supply=currency_amount)

        if self._cache_settings.should_save_to_cache(cache_object=CacheObject.MARKET_DATA_MANAGER):
            self._market_data_manager_cache.save(self.market_data_manager)

        if self._cache_settings.should_save_to_cache(cache_object=CacheObject.GOLD_COST_MANAGER):
            self._gold_cost_manager_cache.save(self.gold_cost_manager)



    def capture(self, currencies: set[Currency]):
        if self._cache_settings.should_load_from_cache(CacheObject.IMAGE_COLLECTIONS_MANAGER):
            image_collections_manager = self._create_manager_from_cache(
                cache=ImageCollectionsManagerCache(),
                cache_object=CacheObject.IMAGE_COLLECTIONS_MANAGER,
                manager_cls=ImageCollectionsManager
            )
            self._process_image_collections(image_collections_manager.image_collections)

        required_data = RequiredDataDeterminer.determine_required_data(
            currencies_to_record=currencies,
            gold_cost_manager=self.gold_cost_manager,
            market_data_manager=self.market_data_manager
        )

        if not required_data.currency_gold_costs and not required_data.currency_pair_market_data:
            return

        bounds_manager = UiBoundsCreator.create_bounds(show=False)
        screen_shot_coordinator = ScreenShotsCoordinator(screen_bounds_manager=bounds_manager)
        for ui_image_collection in screen_shot_coordinator.capture_screen_shots(
            currency_pairs_to_capture=set(required_data.currency_pair_market_data),
            gold_costs_to_capture=set(required_data.currency_gold_costs),
            show=False
        ):
            self._process_image_collections(image_collections=[ui_image_collection])
