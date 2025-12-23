import logging
import re
from dataclasses import dataclass
from enum import Enum
from functools import wraps

import cv2
import numpy as np

from currency_analysis.ui_capture import CurrencyExchangeUiElement, ScreenShotCaptureInterface, ScreenShotCollection, ScreenShot
from currency_analysis.visualizing import Cv2Visualizer


class RatioType(Enum):
    AVAILABLE = 'available'
    COMPETING = 'competing'

@dataclass
class RatioSupply:
    ratio_type: RatioType
    have_currency: str
    want_currency: str
    want_per_have: float
    supply: int

    @property
    def buyout_cost(self) -> float:
        return (1 / self.want_per_have) * self.supply


class CurrencyPair:
    _max_rows = 6

    def __init__(self,
                 have_currency: str,
                 want_currency: str):
        self.have_currency = have_currency
        self.want_currency = want_currency

        self._gold_cost_per_want = None

        self._ratios = []
        self._sorted_ratios = None

        self.atts = dict()

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
            self.atts['sorted_ratios'] = sorted(list(self._ratios), key=lambda r: r.want_per_have)

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

    @property
    def supply_ratios(self) -> list[RatioSupply]:
        return list(self._ratios.values())

    def add_ratio_supply(self,
                         want_per_have: float,
                         stock: int):
        k = want_per_have, stock
        if k in self._ratios:
            r = self._ratios[k]
            r.want_per_have = r.want_per_have or want_per_have
            r.supply = r.supply or stock
        else:
            self._ratios[k] = RatioSupply(ratio_type=self.ratio_type,
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

    def __init__(self,
                 img_array: np.ndarray,
                 logger: logging.Logger):
        self._img_array = img_array
        self._logger = logger

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
                         white_threshold: int = 120) -> "_ImageProcessor":
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

    def __init__(self, logger: logging.Logger):
        self._logger = logger

    def _attempt_to_parse_ratio(self, raw_ratio: str) -> tuple[float, float] | None:
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

    def extract_supply_table(self,
                             img_array: np.ndarray,
                             ratio_type: RatioType,
                             have_currency: str,
                             want_currency: str,
                             num_rows: int = 6) -> _MarketSupplyTable | None:
        img_array = (
            _ImageProcessor(img_array=img_array,
                            logger=self._logger)
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
        for row_array in row_arrays:
            """for thresh in range(80, 120):
                s = (
                    _ImageProcessor(row_array,
                                    logger=self._logger)
                    .grayscale()
                    .show(skip=False)
                    .isolate_outlines()
                    .show(skip=False)
                    .resize(new_size=600)
                    .show(skip=False)
                    .to_string(allowed_chars='0123456789:,.<>')
                )"""
            row_strings = (
                _ImageProcessor(row_array,
                                logger=self._logger)
                .grayscale()
                .isolate_outlines(white_threshold=120)
                .resize(new_size=600)
                .show(skip=False)
                .to_strings(allowed_chars='0123456789:,.<>')
            )
            if not row_strings:
                continue

            supply = row_strings[-1]
            raw_ratio = "".join(row_strings[:-1])
            ratio = self._attempt_to_parse_ratio(raw_ratio)

            table.add_ratio_supply(want_per_have=ratio[0]/ratio[1],
                                   stock=int(supply))

        return table

    def extract_string(self, screen_shot: ScreenShot) -> str | None:
        strings = (
            _ImageProcessor(screen_shot.img_array,
                            logger=self._logger)
            .grayscale()
            .show(skip=False)
            .isolate_outlines()
            .show(skip=False)
            .resize(new_size=600)
            .show(skip=False)
            .to_strings(allowed_chars='0123456789:,.<>')
        )
        return ' '.join(strings)


class MarketDataManager:

    def __init__(self, logger: logging.Logger):
        self._logger = logger

        self._pair_objs = dict()

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


class _MarketDataCaptureManager:

    def __init__(self, logger: logging.Logger):
        self._ui_element_keys = {
            '1': CurrencyExchangeUiElement.WANT_CURRENCY,
            '2': CurrencyExchangeUiElement.HAVE_CURRENCY,
            '3': CurrencyExchangeUiElement.GOLD_COST,
            '4': CurrencyExchangeUiElement.AVAILABLE_TRADES,
            '5': CurrencyExchangeUiElement.COMPETING_TRADES
        }

        self._ui_capture_interface = ScreenShotCaptureInterface(logger=logger)

        self._screen_shot_analyzer = _ScreenShotAnalyzer(logger=logger)
        self._market_data_manager = MarketDataManager(logger=logger)

        self._logger = logger

    def _record_market_data(
            self,
            screen_shot_collection: ScreenShotCollection
    ):
        a = self._screen_shot_analyzer
        c = screen_shot_collection

        # --- Required fields ---
        want_currency = a.extract_string(
            screen_shot=c.fetch_screen_shot(CurrencyExchangeUiElement.WANT_CURRENCY)
        )
        have_currency = a.extract_string(
            screen_shot=c.fetch_screen_shot(CurrencyExchangeUiElement.HAVE_CURRENCY)
        )

        # --- Optional fields ---
        want_currency_amount = a.extract_string(
            screen_shot=c.fetch_screen_shot(ui_element=CurrencyExchangeUiElement.WANT_CURRENCY_AMOUNT)
        ) if c.has_screen_shot(CurrencyExchangeUiElement.WANT_CURRENCY_AMOUNT) else None

        gold_cost = a.extract_string(
            screen_shot=c.fetch_screen_shot(ui_element=CurrencyExchangeUiElement.GOLD_COST)
        ) if c.has_screen_shot(CurrencyExchangeUiElement.GOLD_COST) else None

        available_trades_table = self._screen_shot_analyzer.extract_supply_table(
            img_array=c.fetch_screen_shot(ui_element=CurrencyExchangeUiElement.AVAILABLE_TRADES).img_array,
            ratio_type=RatioType.AVAILABLE,
            have_currency=have_currency,
            want_currency=want_currency
        ) if c.has_screen_shot(CurrencyExchangeUiElement.AVAILABLE_TRADES) else None

        competing_trades_table = self._screen_shot_analyzer.extract_supply_table(
            img_array=c.fetch_screen_shot(ui_element=CurrencyExchangeUiElement.COMPETING_TRADES).img_array,
            ratio_type=RatioType.AVAILABLE,
            have_currency=have_currency,
            want_currency=want_currency
        ) if c.has_screen_shot(CurrencyExchangeUiElement.COMPETING_TRADES) else None

        self._market_data_manager.record_market_data(
            want_currency=want_currency,
            have_currency=have_currency,
            want_currency_amount=want_currency_amount,
            gold_cost=gold_cost,
            available_trades_table=available_trades_table,
            competing_trades_table=competing_trades_table
        )

    def capture(self) -> MarketDataManager:
        self._ui_capture_interface.capture_bounds(ui_elements=[e for e in CurrencyExchangeUiElement])

        for screen_shot_collection in self._ui_capture_interface.capture_screen_shots():
            self._record_market_data(screen_shot_collection=screen_shot_collection)

        return self._market_data_manager
