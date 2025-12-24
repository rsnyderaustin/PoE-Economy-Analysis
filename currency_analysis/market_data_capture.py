import logging
logger = logging.getLogger(__name__)

import string

import pandas as pd
import re
from dataclasses import dataclass
from enum import Enum
from functools import wraps

import cv2
import numpy as np

from currency_analysis.cache import CacheManager, CacheObject, CacheSettings
from currency_analysis.ui_capture import CurrencyExchangeUiElement, ScreenShotsCoordinator, ScreenShotCollection, \
    ScreenShot, ScreenBoundsManager, _ScreenBoundsCapturer, UiBoundsCreator
from currency_analysis.visualizing import Cv2Visualizer


class RatioType(Enum):
    AVAILABLE = 'available'
    COMPETING = 'competing'

@dataclass
class RatioSupply:
    raw_ratio: str
    ratio_type: RatioType
    have_currency: str
    want_currency: str
    want_per_have: float
    supply: int

    def to_dict(self):
        d = self.__dict__
        d['ratio_type'] = d['ratio_type'].value
        return d

    @classmethod
    def from_dict(cls, d: dict):
        d['ratio_type'] = RatioType(d['ratio_type'])
        return cls(**d)

    @property
    def buyout_cost(self) -> float:
        return (1 / self.want_per_have) * self.supply


class CurrencyPair:
    _max_rows = 6

    def __init__(self,
                 have_currency: str,
                 want_currency: str,
                 gold_cost_per_want: float = None,
                 ratios: list[RatioSupply] = None,
                 atts: dict = None):
        self.have_currency = have_currency
        self.want_currency = want_currency

        self._gold_cost_per_want = gold_cost_per_want

        self._ratios = ratios or []
        self._sorted_ratios = None

        self.atts = atts or dict()

    def to_dict(self) -> dict:
        d = self.__dict__.copy()
        d['_ratios'] = [r.to_dict() for r in self._ratios]
        return d

    @classmethod
    def from_dict(cls, d: dict):
        return cls(
            have_currency=d['have_currency'],
            want_currency=d['want_currency'],
            gold_cost_per_want=d.get('gold_cost_per_want'),
            ratios=[RatioSupply.from_dict(ratio_d) for ratio_d in d['ratios']],
            atts=d.get('atts', dict())
        )


    def determine_total_buyout_cost(self):
        """
        :return: The cost to buyout all posted ratios except for the very last
        """
        cls = self.__class__
        return sum(r.buyout_cost for r in self._ratios[:cls._max_rows - 1])

    def determine_total_buyout_supply(self):
        """
        :return: The total supply of all posted ratios except for the very last
        """
        cls = self.__class__
        return sum(r.supply for r in self._ratios[:cls._max_rows - 1])

    @property
    def sorted_ratios(self) -> list[RatioSupply]:
        if 'sorted_ratios' not in self.atts:
            self.atts['sorted_ratios'] = sorted(list(self._ratios), key=lambda r: r.want_per_have, reverse=True)

        return self.atts['sorted_ratios']

    def add_ratios(self, ratio_supplies: list[RatioSupply]):
        for ratio_supply in ratio_supplies:
            if ratio_supply.have_currency != self.have_currency:
                raise ValueError(f"Invalid have currency: {ratio_supply.have_currency}")

            if ratio_supply.want_currency != self.want_currency:
                raise ValueError(f"Invalid want currency: {ratio_supply.want_currency}")

            self._ratios.append(ratio_supply)

    def add_gold_cost(self, gold_cost: int, want_amount: int):
        self._gold_cost_per_want = gold_cost / want_amount


class _MarketSupplyTable:

    def __init__(self,
                 ratio_type: RatioType,
                 have_currency: str,
                 want_currency: str):
        self.ratio_type = ratio_type
        self.have_currency = have_currency
        self.want_currency = want_currency

        self._ratios = dict()

    def print(self):
        ratio_rows = {
            'ratio': [],
            'want_per_have': [],
            'supply': []
        }
        for ratio in self._ratios.values():
            ratio_rows['ratio'].append(ratio.raw_ratio)
            ratio_rows['want_per_have'].append(ratio.want_per_have)
            ratio_rows['supply'].append(ratio.supply)
        df = pd.DataFrame(ratio_rows)
        print(f"Type: {self.ratio_type.value}\nHave: {self.have_currency}\tWant: {self.want_currency}")
        print(df)

    @property
    def supply_ratios(self) -> list[RatioSupply]:
        return list(self._ratios.values())

    def add_ratio_supply(self,
                         raw_ratio: str,
                         want_per_have: float,
                         stock: int):
        k = want_per_have, stock
        if k in self._ratios:
            r = self._ratios[k]
            r.want_per_have = r.want_per_have or want_per_have
            r.supply = r.supply or stock
        else:
            self._ratios[k] = RatioSupply(raw_ratio=raw_ratio,
                                          ratio_type=self.ratio_type,
                                          have_currency=self.have_currency,
                                          want_currency=self.want_currency,
                                          want_per_have=want_per_have,
                                          supply=stock)


def skippable(func):
    """
    Decorator for instance methods that accept a 'skip' boolean keyword argument.
    If skip=True, returns self immediately without calling the method.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if kwargs.get("skip", False):
            return self
        return func(self, *args, **kwargs)

    return wrapper


class _ImageProcessor:

    def __init__(self, img_array: np.ndarray):
        self._img_array = img_array

    @property
    def img_array(self):
        return self._img_array

    @skippable
    def show(self,
             name: str = "Image",
             skip: bool = False) -> "_ImageProcessor":
        Cv2Visualizer.show(self._img_array,
                           name=name)

        return self

    @skippable
    def to_color(self,
                 skip: bool = False) -> "_ImageProcessor":
        self._img_array = cv2.cvtColor(self._img_array,
                                       cv2.COLOR_GRAY2BGR)

        return self

    @skippable
    def grayscale(self,
                  skip: bool = False) -> "_ImageProcessor":
        self._img_array = cv2.cvtColor(self._img_array, cv2.COLOR_BGR2GRAY)
        return self

    @skippable
    def invert_black_white(self,
                           skip: bool = False) -> "_ImageProcessor":
        self._img_array = cv2.bitwise_not(self._img_array)

        return self

    @skippable
    def apply_clahe(self,
                    clip_limit: float = 2.0,
                    tile_size: tuple[int, int] = (8, 8),
                    skip: bool = False) -> "_ImageProcessor":
        clahe = cv2.createCLAHE(clipLimit=clip_limit,
                                tileGridSize=tile_size)
        self._img_array = clahe.apply(self._img_array)

        return self

    @skippable
    def close_gaps(self,
                   grid_size: tuple[int, int] = (2, 2),
                   closure_iterations: int = 1,
                   skip: bool = False) -> "_ImageProcessor":
        kernel = np.ones(grid_size, np.uint8)
        self._img_array = cv2.morphologyEx(
            self._img_array,
            cv2.MORPH_CLOSE,
            kernel,
            iterations=closure_iterations
        )

        return self

    @skippable
    def binarize(self,
                 white_threshold: int = 127,
                 skip: bool = False) -> "_ImageProcessor":
        _, binary = cv2.threshold(self._img_array,
                                  white_threshold,
                                  255,
                                  cv2.THRESH_BINARY)
        self._img_array = binary

        return self

    @skippable
    def dilate(self,
               brush_size: tuple[int, int] = (2, 2),
               iterations: int = 1,
               skip: bool = False) -> "_ImageProcessor":
        kernel = np.ones(brush_size, np.uint8)
        self._img_array = cv2.dilate(self._img_array,
                                     kernel,
                                     iterations=iterations)

        return self

    @skippable
    def isolate_outlines(self,
                         white_threshold: int | None = 120) -> "_ImageProcessor":
        white_threshold = white_threshold or 120
        _, mask = cv2.threshold(
            self._img_array,
            white_threshold,
            255,
            cv2.THRESH_BINARY_INV
        )
        self._img_array = mask
        return self

    @skippable
    def resize(self,
               new_size: int,
               skip: bool = False) -> "_ImageProcessor":
        shape = self._img_array.shape

        if len(shape) == 2:  # grayscale
            curr_height, curr_width = shape
        elif len(shape) == 3:  # color
            curr_height, curr_width = shape[:2]
        scale_factor = new_size / curr_width
        self._img_array = cv2.resize(
            self._img_array,
            None,
            fx=scale_factor,
            fy=scale_factor,
            interpolation=cv2.INTER_LINEAR
        )

        return self

    @skippable
    def to_strings(self,
                   allowed_chars: str,
                   skip: bool = False) -> list[str]:
        import easyocr
        """config = rf'-c tessedit_char_whitelist={allowed_chars} --psm 7'
        text = pytesseract.image_to_string(
            self._img_array,
            config=config
        )"""
        reader = easyocr.Reader(['en'])
        result = reader.readtext(self._img_array,
                                 allowlist=allowed_chars)

        if not result:
            return []

        line = [r[1] for r in sorted(result, key=lambda x: x[0][0][0])]

        return line


class _ScreenShotAnalyzer:
    _SUPPLY_LINE_PATTERN = re.compile(r'^\d+:\d+(?:\.\d+)? \d+$')

    @classmethod
    def _attempt_to_parse_ratio(cls, raw_ratio: str) -> tuple[float, float] | None:
        raw_ratio = re.sub(r'[<>,]', '', raw_ratio)
        raw_ratio = re.sub(r':+', ':', raw_ratio)
        split_done = False
        if ':' in raw_ratio:
            parts = raw_ratio.split(':')
            if len(parts) == 2:
                want = float(parts[0])
                have = float(parts[1])
                return want, have

        if not split_done:
            l_colon_mistake_match = re.search(r"(.*1)\d(.*)", raw_ratio)
            if l_colon_mistake_match:
                left_val = float(l_colon_mistake_match.group(1))
                right_val = float(l_colon_mistake_match.group(2))
                if left_val == 1 or right_val == 1:
                    return left_val, right_val
                elif left_val % 10 == 1:
                    return 1, right_val

        if not split_done:
            r_colon_mistake_match = re.search(r"(.*)\d1", raw_ratio)
            if r_colon_mistake_match:
                want = float(r_colon_mistake_match.group(1))
                have = 1
                return want, have

        return None

    @classmethod
    def extract_supply_table(cls,
                             img_array: np.ndarray,
                             ratio_type: RatioType,
                             have_currency: str,
                             want_currency: str,
                             num_rows: int = 6,
                             show_steps: bool = False) -> _MarketSupplyTable | None:
        img_array = (
            _ImageProcessor(img_array=img_array)
            .resize(new_size=600)
            .img_array
        )
        row_boundaries = np.linspace(0,
                                     img_array.shape[0],
                                     num_rows + 1,
                                     dtype=int)

        row_slices = [(row_boundaries[i], row_boundaries[i + 1]) for i in range(num_rows)]

        """
        draw_img_array = img_array.copy()

        for row_start, row_end in row_slices:
            _Cv2Visualizer.draw_rectangle(
                img_array=draw_img_array,
                x=10,
                y=row_start,
                w=img_array.shape[1] - 20,
                h=row_end - row_start,
                color='red',
                inplace=True,
                thickness=2
            )
        _Cv2Visualizer.show(img_array=draw_img_array)"""

        table = _MarketSupplyTable(ratio_type=ratio_type,
                                   have_currency=have_currency,
                                   want_currency=want_currency)
        row_arrays = [
            img_array[row_start:row_end, :]
            for row_start, row_end in row_slices
        ]
        for row_array in row_arrays[:-1]:
            """for thresh in range(80, 120):
                s = (
                    _ImageProcessor(row_array,
                                    logger=logger)
                    .grayscale()
                    .show(skip=not show_steps)
                    .isolate_outlines()
                    .show(skip=not show_steps)
                    .resize(new_size=600)
                    .show(skip=not show_steps)
                    .to_string(allowed_chars='0123456789:,.<>')
                )"""
            row_strings = (
                _ImageProcessor(row_array)
                .grayscale()
                .isolate_outlines(white_threshold=120)
                .resize(new_size=600)
                .show(skip=not show_steps)
                .to_strings(allowed_chars='0123456789:,.<>')
            )
            if not row_strings:
                continue

            supply = row_strings[-1].replace(',', '')
            if len(row_strings) == 3:
                raw_ratio = f"{row_strings[0]}:{row_strings[1]}"
            else:
                raw_ratio = "".join(row_strings[:-1])

            if not bool(raw_ratio.strip()):
                continue

            ratio = cls._attempt_to_parse_ratio(raw_ratio)
            print(f"Parsed raw ratio {raw_ratio} into {ratio}")

            table.add_ratio_supply(raw_ratio=raw_ratio,
                                   want_per_have=ratio[0]/ratio[1],
                                   stock=int(supply))

        print("Extracted supply table:")
        table.print()
        return table

    @classmethod
    def extract_strings(cls,
                        allowed_chars: str,
                        screen_shot: ScreenShot,
                        white_threshold: int = None,
                        show_steps: bool = False) -> list[str]:
        strings = (
            _ImageProcessor(screen_shot.img_array)
            .grayscale()
            .show(skip=not show_steps)
            .isolate_outlines(white_threshold=white_threshold)
            .show(skip=not show_steps)
            .resize(new_size=600)
            .show(skip=not show_steps)
            .to_strings(allowed_chars=allowed_chars)
        )
        print(f"Extracted {strings}")
        return strings


class MarketDataManager:

    def __init__(self,
                 currency_pairs: list[CurrencyPair] = None):
        self._pair_objs = {(p.have_currency, p.want_currency): p for p in currency_pairs} if currency_pairs else dict()

    def to_dict(self) -> dict:
        return {'pair_objs': [p.to_dict() for k, p in self._pair_objs.items()]}

    @classmethod
    def from_dict(cls, d: dict) -> "MarketDataManager":
        pair_objs = [CurrencyPair.from_dict(pair_d) for pair_d in d['pair_objs']]
        return MarketDataManager(currency_pairs=pair_objs)


    def fetch_currency_pair_objs(self) -> list[CurrencyPair]:
        return list(self._pair_objs.values())

    def record_market_data(self,
                           want_currency: str,
                           have_currency: str,
                           gold_cost: int = None,
                           want_currency_amount: int = None,
                           available_trades_table: _MarketSupplyTable | None = None,
                           competing_trades_table: _MarketSupplyTable | None = None):
        k = have_currency, want_currency
        if k not in self._pair_objs:
            self._pair_objs[k] = CurrencyPair(have_currency=have_currency,
                                              want_currency=want_currency)
        pair_obj = self._pair_objs[k]

        if available_trades_table:
            pair_obj.add_ratios(available_trades_table.supply_ratios)

        if competing_trades_table:
            pair_obj.add_ratios(competing_trades_table.supply_ratios)

        if gold_cost and want_currency_amount:
            pair_obj.add_gold_cost(gold_cost=gold_cost,
                                   want_amount=want_currency_amount)

class MarketDataCaptureManager:

    def __init__(self,
                 cache_settings: CacheSettings):
        self._cache_settings = cache_settings

        self._market_data_manager = None
        if self._cache_settings.should_load_from_cache(CacheObject.MARKET_DATA_MANAGER):
            self._market_data_manager = CacheManager.load_from_cache(cache_object=CacheObject.MARKET_DATA_MANAGER)
        if not self._market_data_manager:
            self._market_data_manager = MarketDataManager()

        self._screen_shot_analyzer = _ScreenShotAnalyzer()
        self._market_data_manager = MarketDataManager()

    def _record_market_data(
            self,
            screen_shot_collection: ScreenShotCollection
    ):
        print("Recording market data...")
        a = self._screen_shot_analyzer
        c = screen_shot_collection

        currency_allowed_chars = f"{string.ascii_letters} "
        # --- Required fields ---
        print("\tExtracting Want Currency string...")
        want_currency_strings = a.extract_strings(
            screen_shot=c.fetch_screen_shot(CurrencyExchangeUiElement.WANT_CURRENCY),
            allowed_chars=currency_allowed_chars
        )
        want_currency = ''.join(want_currency_strings)

        print("\tExtracting Have Currency string...")
        have_currency_strings = a.extract_strings(
            screen_shot=c.fetch_screen_shot(CurrencyExchangeUiElement.HAVE_CURRENCY),
            allowed_chars=currency_allowed_chars
        )
        have_currency = ''.join(have_currency_strings)

        if c.has_screen_shot(CurrencyExchangeUiElement.WANT_CURRENCY_AMOUNT):
            print("\tExtracting Want Currency Amount string...")
            want_currency_amount_strings = a.extract_strings(
                screen_shot=c.fetch_screen_shot(ui_element=CurrencyExchangeUiElement.WANT_CURRENCY_AMOUNT),
                allowed_chars='1234567890',
                white_threshold=100,
                show_steps=True
            )
            want_currency_amount = int(''.join(want_currency_amount_strings))
        else:
            want_currency_amount = None

        if c.has_screen_shot(CurrencyExchangeUiElement.GOLD_COST):
            print("\tExtracting Gold Cost string...")
            gold_cost_strings = a.extract_strings(
                screen_shot=c.fetch_screen_shot(ui_element=CurrencyExchangeUiElement.GOLD_COST),
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

        if c.has_screen_shot(CurrencyExchangeUiElement.AVAILABLE_TRADES):
            print("\tExtracting Available Trades table...")
            available_trades_table = self._screen_shot_analyzer.extract_supply_table(
                img_array=c.fetch_screen_shot(ui_element=CurrencyExchangeUiElement.AVAILABLE_TRADES).img_array,
                ratio_type=RatioType.AVAILABLE,
                have_currency=have_currency,
                want_currency=want_currency
            )
        else:
            available_trades_table = None

        if c.has_screen_shot(CurrencyExchangeUiElement.COMPETING_TRADES):
            print("\tExtracting Competing Trades table")
            competing_trades_table = self._screen_shot_analyzer.extract_supply_table(
                img_array=c.fetch_screen_shot(ui_element=CurrencyExchangeUiElement.COMPETING_TRADES).img_array,
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
        
    def _create_market_data_manager(self) -> MarketDataManager:
        market_data_manager = None
        if self._cache_settings.should_load_from_cache(CacheObject.MARKET_DATA_MANAGER):
            market_data_manager = CacheManager.load_from_cache(cache_object=CacheObject.MARKET_DATA_MANAGER)
        if not market_data_manager:
            market_data_manager = MarketDataManager()
        
        return market_data_manager
            
    """def _create_bounds_manager(self) -> ScreenBoundsManager:
        bounds_manager = None
        if self._cache_settings.should_load_from_cache(cache_object=CacheObject.CAPTURE_BOUNDS):
            bounds_manager_data = CacheManager.load_from_cache(cache_object=CacheObject.CAPTURE_BOUNDS)
            if bounds_manager_data:
                bounds_manager = ScreenBoundsManager.from_dict(bounds_manager_data)

        if not bounds_manager:
            bounds_capturer = ScreenBoundsCapturer(bounds_manager=ScreenBoundsManager())
            bounds_manager = bounds_capturer.capture_bounds()

            if self._cache_settings.should_save_to_cache(cache_object=CacheObject.CAPTURE_BOUNDS):
                CacheManager.save_to_cache(d=bounds_manager.to_dict(),
                                           cache_object=CacheObject.CAPTURE_BOUNDS)

        return bounds_manager"""

    def capture(self) -> MarketDataManager:
        bounds_manager = UiBoundsCreator.create_bounds(show=False)
        screen_shot_capturer = ScreenShotsCoordinator(screen_bounds_manager=bounds_manager)

        for screen_shot_collection in screen_shot_capturer.capture_screen_shots():
            self._record_market_data(screen_shot_collection=screen_shot_collection)

            if self._cache_settings.should_save_to_cache(CacheObject.MARKET_DATA_MANAGER):
                logger.info("Saving to cache...")
                CacheManager.save_to_cache(self._market_data_manager.to_dict(),
                                           cache_object=CacheObject.MARKET_DATA_MANAGER)
                logger.info("\tFinished saving to cache")

        return self._market_data_manager
