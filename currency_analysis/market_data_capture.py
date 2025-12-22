import math
import re
from dataclasses import dataclass
from enum import Enum
import logging
from functools import wraps
from pprint import pprint
import pandas as pd
import time
import cv2

import mss
import numpy as np
import pytesseract
import easyocr
from PIL import Image as PILImage
from io import BytesIO
from pynput import mouse, keyboard
from pytesseract import Output


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
        print(f"\tListening for key press...")
        listener = keyboard.Listener(on_press=self._on_press)
        listener.start()

        while self._captured_char is None:
            time.sleep(0.5)

        listener.stop()

        return self._captured_char


class _ScreenShotCapturer:

    @staticmethod
    def capture(bounds: _CaptureBounds):
        with mss.mss() as sct:
            region = {
                "left": bounds.x_min,
                "top": bounds.y_min,
                "width": bounds.width,
                "height": bounds.height
            }
            img = np.array(sct.grab(region))

            return img


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

    def __init__(self, screen_shots: dict[_MarketUiElement: np.ndarray]):
        missing_ui_elements = ui_element_enums - set(screen_shots.keys())
        if missing_ui_elements:
            raise ValueError(f"Missing bounds types {missing_ui_elements}")

        self._screen_shots = screen_shots

    def fetch_screen_shot(self, ui_element: _MarketUiElement) -> np.ndarray:
        return self._screen_shots[ui_element]

@dataclass
class _RatioSupply:
    have_currency: str
    want_currency: str
    haves_per_want: float = None
    supply: int = None

class _MarketSupplyTable:

    def __init__(self,
                 have_currency: str,
                 want_currency: str):
        self._have_currency = have_currency
        self._want_currency = want_currency

        self._ratios = dict()

    def sort_ratio_supply_objs(self, reverse: bool = False) -> list[_RatioSupply]:
        return sorted(self._ratios.values(), key=lambda r: r.haves_per_want, reverse=reverse)

    def add_ratio_supply(self,
                         cost_per_have: float = None,
                         stock: int = None):
        k = cost_per_have, stock
        if k in self._ratios:
            r = self._ratios[k]
            r.haves_per_want = r.haves_per_want or cost_per_have
            r.supply = r.supply or stock
        else:
            self._ratios[k] = _RatioSupply(have_currency=self._have_currency,
                                           want_currency=self._want_currency,
                                           haves_per_want=cost_per_have,
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
    def split_into_parts(self,
                         show_algorithm: bool) -> list["_ImageProcessor"]:
        img_array = (
            _ImageProcessor(img_array=self._img_array.copy(),
                            logger=self._logger)
            .resize(new_size=600)
            .close_gaps(closure_iterations=1)
            .binarize()
            .show(name='split into parts prep')
            .img_array
        )
        display_img_array = (
            _ImageProcessor(img_array=img_array.copy(),
                            logger=self._logger)
            .to_color()
            .img_array
        )

        self._logger.info("Splitting table into parts...")
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
            img_array,
            connectivity=8
        )
        self._logger.info(f"\tFinished splitting table. Split into {num_labels - 1} parts")

        if show_algorithm:
            self._logger.info("Drawing split image parts...")
            for i in range(1, num_labels):
                x, y, w, h, area = stats[i]
                _Cv2Visualizer.draw_rectangle(
                    img_array=display_img_array,
                    x=x,
                    y=y,
                    w=w,
                    h=h,
                    color='red',
                    thickness=5,
                    inplace=True
                )
            self._logger.info(f"\tFinished drawing split image parts.")

            _Cv2Visualizer.show(img_array=display_img_array,
                                name='drawn parts')

        merged = []
        current = list(stats[0])
        for x, y, w, h, area in stats[1:]:
            curr_x, curr_y, curr_w, curr_h, curr_area = current

            if show_algorithm:
                temp_img_array = _Cv2Visualizer.draw_rectangle(
                    img_array=display_img_array,
                    x=curr_x,
                    y=curr_y,
                    w=10,
                    h=8,
                    color='red',
                    inplace=False
                )
                _Cv2Visualizer.show(img_array=temp_img_array)

            # same line + close horizontally
            if abs(y - curr_y) < 10 and x <= curr_x + curr_w + 8:
                # merge
                new_x = min(curr_x, x)
                new_y = min(curr_y, y)
                new_w = max(curr_x + curr_w, x + w) - new_x
                new_h = max(curr_y + curr_h, y + h) - new_y
                current = [new_x, new_y, new_w, new_h]
            else:
                merged.append(tuple(current))
                current = [x, y, w, h]

        merged.append(tuple(current))

        split_processors = []
        for x, y, w, h in merged:
            split_processors.append(
                _ImageProcessor(
                    img_array=img_array[y:y + h, x:x + w],
                    logger=self._logger
                )
            )

        return split_processors

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
                         white_threshold: int = 100) -> "_ImageProcessor":
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
        curr_width, curr_height = self._img_array.shape
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
        reader = easyocr.Reader(['en'], gpu=False)  # gpu=True if you have CUDA

        results = reader.readtext(self._img_array,
                                  detail=0,
                                  allowlist=allowed_chars)
        return results


class _ScreenShotAnalyzer:

    _SUPPLY_LINE_PATTERN = re.compile(r'^\d+:\d+(?:\.\d+)? \d+$')

    def __init__(self, logger: logging.Logger):
        self._logger = logger

    def _preprocess(self, screen_shot: np.ndarray) -> PILImage:
        # Convert mss BGRA to PIL RGB
        img = PILImage.fromarray(screen_shot[:, :, :3])

        # Convert to grayscale
        img = img.convert('L')

        return img

    def _extract_text(self, img) -> str:
        text = pytesseract.image_to_string(img, config='--psm 6')  # psm 7 = single line
        formatted_text = text.replace('\n', ' ').strip()
        self._logger.info(f"Extracted text from image: {formatted_text}")
        return formatted_text

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
                              want_currency: str) -> _MarketSupplyTable | None:


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
    def analyze_for_string(self, screen_shot: np.ndarray) -> str | None:
        print(f"Analyzing screen shot for string...")
        preprocessed_image = self._preprocess(screen_shot)
        r = self._extract_text(preprocessed_image)
        print("\tFinished analyzing screen shot for string.")
        return r

    def analyze_for_table(self,
                          screen_shot: np.ndarray,
                          have_currency: str,
                          want_currency: str) -> _MarketSupplyTable | None:
        print(f"Analyzing screen shot for table...")
        r = self._extract_supply_table(screen_shot,
                                       have_currency=have_currency,
                                       want_currency=want_currency)
        print("\tFinished analyzing screen shot for table.")
        return r


class _MarketDataManager:

    def __init__(self, logger: logging.Logger):
        self._logger = logger

        self._market_data = dict()

    def record_market_data(self,
                           want_currency: str,
                           have_currency: str,
                           gold_cost: int | None = None,
                           available_trades_table: _MarketSupplyTable | None = None,
                           competing_trades_table: _MarketSupplyTable | None = None):
        if have_currency not in self._market_data:
            self._market_data[have_currency] = dict()

        available_ratios = available_trades_table.sort_ratio_supply_objs(reverse=True)
        if available_trades_table and not available_ratios:
            self._logger.error(f"No available trades found for converting {have_currency} to {want_currency}")
            return

        competing_ratios = competing_trades_table.sort_ratio_supply_objs(reverse=True)
        if competing_trades_table and not competing_ratios:
            self._logger.error(f"No competing trades found for converting {have_currency} to {want_currency}")
            return

        self._market_data[have_currency][want_currency] = available_ratios[0].haves_per_want

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
        self._market_data_manager = _MarketDataManager(logger=logger)

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
            screen_shot=screen_shot_collection.fetch_screen_shot(ui_element=_MarketUiElement.AVAILABLE_TRADES),
            have_currency=have_currency,
            want_currency=want_currency
        )
        competing_trades_table = screen_shot_analyzer.analyze_for_table(
            screen_shot=screen_shot_collection.fetch_screen_shot(ui_element=_MarketUiElement.COMPETING_TRADES),
            have_currency=have_currency,
            want_currency=want_currency
        )
        self._market_data_manager.record_market_data(
            want_currency=want_currency,
            have_currency=have_currency,
            available_trades_table=available_trades_table,
            competing_trades_table=competing_trades_table
        )


    def capture(self):
        self._capture_bounds()

        screen_shot_analyzer = _ScreenShotAnalyzer(logger=self._logger)
        for screen_shot_collection in self._capture_screen_shots():
            self._record_market_data(screen_shot_analyzer=screen_shot_analyzer,
                                     screen_shot_collection=screen_shot_collection)
        x=0

