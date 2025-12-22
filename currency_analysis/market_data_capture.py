import math
import re
from dataclasses import dataclass
from enum import Enum
import logging
from functools import wraps
from pprint import pprint
import time
import cv2

import numpy as np


@dataclass(frozen=True)
class _CaptureBounds:
    x_min: int
    y_min: int
    x_max: int
    y_max: int

    @property
    def height(self) -> int:
        return int(self.y_max - self.y_min)

    @property
    def width(self) -> int:
        return int(self.x_max - self.x_min)

class _MarketUiElement(Enum):
    WANT_CURRENCY = 'Want Currency'
    HAVE_CURRENCY = 'Have Currency'
    # GOLD_COST = 'Gold Cost'
    AVAILABLE_TRADES = 'Available Trades'
    COMPETING_TRADES = 'Competing Trades'

ui_element_enums = set(e for e in _MarketUiElement)

class _ScreenBoundsCapturer:

    def __init__(self,
                 ui_element: _MarketUiElement):
        self._ui_element = ui_element

        self._click_point_start = None
        self._click_point_end = None

    def _on_click(self, x, y, button, pressed):
        if not pressed:
            print(f"\tDetected Screen Capture click at ({x}, {y})")
            if self._click_point_start is None:
                self._click_point_start = x, y
            else:
                self._click_point_end = x, y
            
            return False
        
        return True

    def capture(self) -> _CaptureBounds | None:
        from pynput import mouse

        with mouse.Listener(on_click=self._on_click) as listener:
            print(f"Click to select the first corner of {self._ui_element.value}...")
            listener.join()

        with mouse.Listener(on_click=self._on_click) as listener:
            print(f"Click to select the second corner of {self._ui_element.value}...")
            listener.join()

        print(f"\tFinished listening for the region for {self._ui_element.value}")

        return _CaptureBounds(
            x_min=min(self._click_point_start[0], self._click_point_end[0]),
            y_min=min(self._click_point_start[1], self._click_point_end[1]),
            x_max=max(self._click_point_start[0], self._click_point_end[0]),
            y_max=max(self._click_point_start[1], self._click_point_end[1])
        )

class _KeyPressCapturer:

    def __init__(self, acceptable_keys: set[str]):
        self._acceptable_keys = acceptable_keys

        self._captured_char = None

    def _on_press(self, key):
        try:
            if key.char in self._acceptable_keys:
                print(f"\tDetected acceptable key press for {key.char}")
                self._captured_char = key.char
                return False
            else:
                print(f"\tDetected unacceptable key press for {key.char}")
        except AttributeError:
            print(f"\tInvalid character key press {key}")

    def capture(self) -> str | None:
        from pynput import keyboard

        print(f"\tListening for key press...")
        listener = keyboard.Listener(on_press=self._on_press)
        listener.start()

        while self._captured_char is None:
            time.sleep(0.5)

        listener.stop()

        return self._captured_char


@dataclass(frozen=True)
class _ScreenShot:
    img_array: np.ndarray
    x_min: int
    y_min: int
    x_max: int
    y_max: int


class _ScreenShotCapturer:

    @staticmethod
    def capture(bounds: _CaptureBounds) -> _ScreenShot:
        import mss
        with mss.mss() as sct:
            region = {
                "left": bounds.x_min,
                "top": bounds.y_min,
                "width": bounds.width,
                "height": bounds.height
            }
            img = np.array(sct.grab(region))

            return _ScreenShot(
                img_array=img,
                x_min=bounds.x_min,
                y_min=bounds.y_min,
                x_max=bounds.x_max,
                y_max=bounds.y_max
            )


class _ScreenBoundsManager:

    def __init__(self,
                 expected_bounds: set[_MarketUiElement],
                 logger: logging.Logger):
        self._bounds = {bound: None for bound in expected_bounds}
        self._logger = logger

    @property
    def all_bounds_filled(self):
        return all(v is not None for v in self._bounds.values())

    @property
    def filled_ui_elements(self) -> list[_MarketUiElement]:
        return [ui_element for ui_element, bounds in self._bounds.items()
                if bounds is not None]

    def add_bounds(self, ui_element: _MarketUiElement, bounds: _CaptureBounds):
        if ui_element not in self._bounds:
            raise ValueError(f"Invalid bounds type {ui_element}")

        if self._bounds[ui_element] is not None:
            self._logger.warning(f"Bounds {ui_element} already exists. Overwriting...")

        self._bounds[ui_element] = bounds

    def fetch_bounds(self, ui_element: _MarketUiElement) -> _CaptureBounds | None:
        return self._bounds.get(ui_element, None)


class _ScreenShotCollection:

    def __init__(self, screen_shots: dict[_MarketUiElement: _ScreenShot]):
        self._screen_shots = screen_shots

    def fetch_screen_shot(self, ui_element: _MarketUiElement) -> _ScreenShot:
        if ui_element not in self._screen_shots:
            raise ValueError(f"UiElement {ui_element} ScreenShot not in self._screen_shots")

        return self._screen_shots[ui_element]


@dataclass
class RatioSupply:
    have_currency: str
    want_currency: str
    want_per_have: float
    supply: int

    @property
    def buyout_cost(self) -> float:
        return (1 / self.want_per_have) * self.supply


class CurrencyPairRates:

    def __init__(self,
                 have_currency: str,
                 want_currency: str):
        self.have_currency = have_currency
        self.want_currency = want_currency

        self._ratios = []
        self._sorted_ratios = None

        self.atts = dict()

    def to_df(self):
        rows = {
            'have_currency': [],
            'want_currency': [],
            'tier': [],
            'want_per_have': [],
            'max_have': [],
            'prev_cum_have': [],
            'max_want': []
        }

        for (have_currency, want_currency), ratio_objs in ratios.items():
            tier = 0
            cum_have = 0
            for i, ratio_obj in enumerate(ratio_objs):
                rows['have_currency'].append(have_currency)
                rows['want_currency'].append(want_currency)
                rows['tier'].append(tier)
                rows['want_per_have'].append(ratio_obj.want_per_have)

                # For the worst posted ratio, but we just assume an infinite supply
                if i == len(ratio_objs) - 1:
                    max_have = 999e3
                    max_want = 999e3
                else:
                    max_have = (1 / ratio_obj.want_per_have) * ratio_obj.supply
                    max_want = ratio_obj.supply

                rows['max_have'].append(max_have)
                rows['max_want'].append(max_want)
                rows['prev_cum_have'] = cum_have

                cum_have += max_have

                cum_have += ratio_obj.supply
                tier += 1

        return pd.DataFrame(rows)

    @property
    def sorted_ratios(self) -> list[RatioSupply]:
        if 'sorted_ratios' not in self.atts:
            self.atts['sorted_ratios'] = sorted(list(self._ratios), key=lambda r:r.want_per_have)

        return self.atts['sorted_ratios']

    def add_ratios(self, ratio_supplies: list[RatioSupply]):
        for ratio_supply in ratio_supplies:
            if ratio_supply.have_currency != self.have_currency:
                raise ValueError(f"Invalid have currency: {ratio_supply.have_currency}")

            if ratio_supply.want_currency != self.want_currency:
                raise ValueError(f"Invalid want currency: {ratio_supply.want_currency}")

            self._ratios.append(ratio_supply)

    def _group_into_dict(self, ratios: list[RatioSupply]) -> dict:
        ratios = dict()
        for r in ratios:
            k = r.have_currency, r.want_currency
            if k not in ratios:
                ratios[k] = list()
            ratios[k].append(r)

        for currencies, ratio_objs in ratios.items():
            ratios[currencies] = sorted(ratio_objs, key=lambda r: r.want_per_have)

        return ratios


class _MarketSupplyTable:

    def __init__(self,
                 have_currency: str,
                 want_currency: str):
        self._have_currency = have_currency
        self._want_currency = want_currency

        self._ratios = dict()

    @property
    def supply_ratios(self, reverse: bool = False) -> list[RatioSupply]:
        return list(self._ratios.values())

    def add_ratio_supply(self,
                         cost_per_have: float = None,
                         stock: int = None):
        k = cost_per_have, stock
        if k in self._ratios:
            r = self._ratios[k]
            r.want_per_have = r.want_per_have or cost_per_have
            r.supply = r.supply or stock
        else:
            self._ratios[k] = RatioSupply(have_currency=self._have_currency,
                                          want_currency=self._want_currency,
                                          want_per_have=cost_per_have,
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

class _Cv2Visualizer:

    _colors = {
        'red': (255, 0, 0),
        'green': (0, 255, 0),
        'blue': (0, 0, 255),
    }

    @classmethod
    def show(cls,
             img_array: np.ndarray,
             name: str = "Image"):
        cv2.imshow(name, img_array)
        cv2.waitKey(0)

    @classmethod
    def draw_rectangle(cls,
                       img_array: np.ndarray,
                       x, y, w, h,
                       color: str,
                       inplace: bool,
                       thickness: int = 1) -> np.ndarray | None:
        img_array = img_array if inplace else img_array.copy()

        color_nums = cls._colors[color]
        cv2.rectangle(img_array,
                      (x, y),
                      (x + w, y + h),
                      color=color_nums,
                      thickness=thickness)

        if not inplace:
            return img_array

        return None

    def draw_circle(self,
                    img_array: np.ndarray,
                    cx, cy, r):
        cv2.circle(img_array,
                   (cx, cy),
                   r,
                   (0, 255, 0),
                   1)

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
        _Cv2Visualizer.show(self._img_array,
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
    def to_string(self,
                  allowed_chars: str,
                  skip: bool = False) -> list[str]:
        import easyocr
        """config = rf'-c tessedit_char_whitelist={allowed_chars} --psm 7'
        text = pytesseract.image_to_string(
            self._img_array,
            config=config
        )"""
        reader = easyocr.Reader(['en'])
        result = reader.readtext(self._img_array)

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

    def _extract_supply_table(self,
                              img_array: np.ndarray,
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
        draw_img_array = img_array.copy()

        """for row_start, row_end in row_slices:
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

        row_arrays = [
            img_array[row_start:row_end, :]
            for row_start, row_end in row_slices
        ]
        for row_array in row_arrays:
            for thresh in range(80, 120):
                """s = (
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
            s = (
                _ImageProcessor(row_array,
                                logger=self._logger)
                .grayscale()
                .isolate_outlines(white_threshold=120)
                .resize(new_size=600)
                .show(skip=False)
                .to_string(allowed_chars='0123456789:,.<>')
            )
            print(s)

        """table_texts = [re.sub(r'[,<>]', '', t) for t in table_texts]

        print(f"Analyzing table texts: {table_texts}")

        table = _MarketSupplyTable(have_currency=have_currency,
                                   want_currency=want_currency)
        print(f"Raw supply table:")
        for pair_i in range(math.ceil(len(table_texts) / 2)):
            raw_ratio = table_texts[pair_i * 2]
            raw_supply = table_texts[pair_i * 2 + 1]

            try:
                ratio = self._attempt_to_parse_ratio(raw_ratio)
            except ValueError:
                continue

            if not ratio:
                print(f"{raw_ratio}, {raw_supply} -> INVALID")
                return None

            want, have = ratio

            supply = int(raw_supply)
            print(f"{raw_ratio}, {raw_supply} -> {want}:{have}, Supply: {supply}")
            table.add_ratio_supply(cost_per_have=float(have / want),
                                   stock=supply)

        return table
"""
    def analyze_for_string(self, screen_shot: _ScreenShot) -> str | None:
        img_array = screen_shot.img_array
        print(f"Analyzing screen shot for string...")
        preprocessed_image = self._preprocess(img_array)
        r = self._extract_text(preprocessed_image)
        print("\tFinished analyzing screen shot for string.")
        return r

    def analyze_for_table(self,
                          img_array: np.ndarray,
                          have_currency: str,
                          want_currency: str) -> _MarketSupplyTable | None:
        print(f"Analyzing screen shot for table...")
        r = self._extract_supply_table(img_array,
                                       have_currency=have_currency,
                                       want_currency=want_currency)
        print("\tFinished analyzing screen shot for table.")
        return r


class MarketDataManager:

    def __init__(self, logger: logging.Logger):
        self._logger = logger

        self._market_data = dict()

    def fetch_currency_pair_objs(self) -> list[CurrencyPairRates]:
        return_ratio_objs = []
        for want_currency, have_currency_ratio_objs in self._market_data.items():
            for have_currency, ratio_objs in have_currency_ratio_objs.items():
               return_ratio_objs.extend(ratio_objs)

        return return_ratio_objs

    def record_market_data(self,
                           want_currency: str,
                           have_currency: str,
                           available_trades_table: _MarketSupplyTable | None = None,
                           competing_trades_table: _MarketSupplyTable | None = None):
        if want_currency not in self._market_data:
            self._market_data[want_currency] = dict()

        available_ratios = available_trades_table.supply_ratios
        if available_trades_table and not available_ratios:
            self._logger.error(f"No available trades found for '{have_currency}' -> '{want_currency}'")
            return

        competing_ratios = competing_trades_table.supply_ratios
        if competing_trades_table and not competing_ratios:
            self._logger.error(f"No competing trades found for '{have_currency}' -> '{want_currency}'")
            return

        pair_rates_obj = CurrencyPairRates(have_currency=have_currency,
                                           want_currency=want_currency)
        pair_rates_obj.add_ratios(available_ratios)

        self._market_data[want_currency][have_currency] = pair_rates_obj


class _MarketDataCaptureManager:

    def __init__(self, logger: logging.Logger):
        self._ui_element_keys = {
            '1': _MarketUiElement.WANT_CURRENCY,
            '2': _MarketUiElement.HAVE_CURRENCY,
            # '3': _MarketUiElement.GOLD_COST,
            '4': _MarketUiElement.AVAILABLE_TRADES,
            '5': _MarketUiElement.COMPETING_TRADES
        }

        self._screen_bounds_manager = _ScreenBoundsManager(logger=logger,
                                                           expected_bounds=set(self._ui_element_keys.values()))
        self._market_data_manager = MarketDataManager(logger=logger)

        self._logger = logger

    def _capture_bounds(self):
        print(f"Calibrating bounds...")

        while not self._screen_bounds_manager.all_bounds_filled:
            print("\n")
            captured_bounds = self._screen_bounds_manager.filled_ui_elements
            if captured_bounds:
                print(f"Captured bounds thus far: {[b.value for b in captured_bounds]}")

            print(f"Press a key from below to begin capturing bounds:")
            pprint({k: v.value for k, v in self._ui_element_keys.items()})

            key_press = _KeyPressCapturer(acceptable_keys=set(self._ui_element_keys.keys())).capture()
            if key_press in self._ui_element_keys:
                char = key_press

                ui_element = self._ui_element_keys[char]
                bounds = _ScreenBoundsCapturer(ui_element=ui_element).capture()

                self._screen_bounds_manager.add_bounds(ui_element=ui_element, bounds=bounds)

            else:
                print(f"Key pressed '{key_press}' not one of acceptable keys {list(self._ui_element_keys.keys())}"
                      f"\nTry again...")

        print("Finished calibrating.\n")

    def _capture_screen_shots(self):
        pressed_key = None
        while pressed_key != 'c':
            print("Press 'c' to capture...")
            pressed_key = _KeyPressCapturer(acceptable_keys={'c'}).capture()

        screen_shots = {
            ui_element: _ScreenShotCapturer.capture(bounds=self._screen_bounds_manager.fetch_bounds(ui_element))
            for ui_element in ui_element_enums
        }
        collection = _ScreenShotCollection(screen_shots=screen_shots)

        print('Successfully captured screen shots.')

        yield collection

    def _record_market_data(self,
                            screen_shot_analyzer: _ScreenShotAnalyzer,
                            screen_shot_collection: _ScreenShotCollection):
        want_currency = screen_shot_analyzer.analyze_for_string(
            screen_shot=screen_shot_collection.fetch_screen_shot(ui_element=_MarketUiElement.WANT_CURRENCY)
        )
        have_currency = screen_shot_analyzer.analyze_for_string(
            screen_shot=screen_shot_collection.fetch_screen_shot(ui_element=_MarketUiElement.HAVE_CURRENCY)
        )
        """gold_cost = screen_shot_analyzer.analyze_for_string(
            screen_shot=screen_shot_collection.fetch_screen_shot(ui_element=_MarketUiElement.GOLD_COST)
        )"""
        available_trades_table = screen_shot_analyzer.analyze_for_table(
            img_array=screen_shot_collection.fetch_screen_shot(ui_element=_MarketUiElement.AVAILABLE_TRADES).img_array,
            have_currency=have_currency,
            want_currency=want_currency
        )
        competing_trades_table = screen_shot_analyzer.analyze_for_table(
            img_array=screen_shot_collection.fetch_screen_shot(ui_element=_MarketUiElement.COMPETING_TRADES).img_array,
            have_currency=have_currency,
            want_currency=want_currency
        )
        self._market_data_manager.record_market_data(
            want_currency=want_currency,
            have_currency=have_currency,
            available_trades_table=available_trades_table,
            competing_trades_table=competing_trades_table
        )


    def capture(self) -> MarketDataManager:
        self._capture_bounds()

        screen_shot_analyzer = _ScreenShotAnalyzer(logger=self._logger)
        for screen_shot_collection in self._capture_screen_shots():
            self._record_market_data(screen_shot_analyzer=screen_shot_analyzer,
                                     screen_shot_collection=screen_shot_collection)

        return self._market_data_manager
