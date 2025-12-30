import datetime
import logging
import uuid
from abc import ABC
from typing import Iterable

from currency_analysis import utils
from currency_analysis.data_objects import Currency

logger = logging.getLogger(__name__)
import time
from dataclasses import dataclass
from enum import Enum

import numpy as np
from pynput import keyboard

from currency_analysis.visualizing import Cv2Visualizer


class UiElement(Enum):
    AVAILABLE_TRADES = 'Available Trades'
    TRADES_SOLO_TABLE = 'Trades Solo Table'
    COMPETING_TRADES = 'Competing Trades'


@dataclass(frozen=True)
class RelativeBounds:
    pct_width: float
    pct_height: float
    pct_from_x_min: float
    pct_from_y_min: float


class CaptureBounds:

    def __init__(self,
                 x_min: int,
                 y_min: int,
                 x_max: int,
                 y_max: int):
        self.x_min = x_min
        self.y_min = y_min
        self.x_max = x_max
        self.y_max = y_max

    def to_dict(self) -> dict:
        d = self.__dict__.copy()
        d['ui_element'] = d['ui_element'].value
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "CaptureBounds":
        d['ui_element'] = UiElement(d['ui_element'])
        return CaptureBounds(**d)

    @property
    def height(self) -> int:
        return int(self.y_max - self.y_min)

    @property
    def width(self) -> int:
        return int(self.x_max - self.x_min)


class CaptureTableBounds:

    def __init__(self, x_min: int, y_min: int, x_max: int, y_max: int, num_rows: int = 6):
        self.ratio_bounds, self.stock_bounds = self._split_into_row_bounds(
            x_min=x_min,
            y_min=y_min,
            x_max=x_max,
            y_max=y_max,
            num_rows=num_rows
        )

        self.x_min = x_min
        self.y_min = y_min
        self.x_max = x_max
        self.y_max = y_max

        self.num_rows = num_rows

    def _split_into_row_bounds(self,
                               x_min: int,
                               y_min: int,
                               x_max: int,
                               y_max: int,
                               num_rows: int) -> tuple[list[CaptureBounds], list[CaptureBounds]]:
        row_boundaries = list(np.linspace(
            y_min,
            y_max,
            num_rows + 1,
            dtype=int
        ))

        row_slices = [(row_boundaries[i], row_boundaries[i + 1])
                      for i in range(num_rows)]

        col_slice = int((x_max + x_min) / 2)
        ratio_bounds = [
            CaptureBounds(x_min=x_min,
                          y_min=row_slice[0],
                          x_max=col_slice,
                          y_max=row_slice[1])
            for row_slice in row_slices
        ]
        stock_bounds = [
            CaptureBounds(x_min=col_slice,
                          y_min=row_slice[0],
                          x_max=x_max,
                          y_max=row_slice[1])
            for row_slice in row_slices
        ]

        return ratio_bounds, stock_bounds


class _ScreenBoundsCapturer:

    def __init__(self):
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

    def capture(self) -> CaptureBounds:
        from pynput import mouse

        with mouse.Listener(on_click=self._on_click) as listener:
            print("Click to select the top left capture corner")
            listener.join()

        with mouse.Listener(on_click=self._on_click) as listener:
            print(f"Click to select the bottom right capture corner")
            listener.join()

        while True:
            key = input(f"1: Take a sample screen shot\n2: Recapture bounds\n3: Continue\nEnter choice:")

            if key == '2':
                self.capture()

            bounds = CaptureBounds(
                x_min=min(self._click_point_start[0], self._click_point_end[0]),
                y_min=min(self._click_point_start[1], self._click_point_end[1]),
                x_max=max(self._click_point_start[0], self._click_point_end[0]),
                y_max=max(self._click_point_start[1], self._click_point_end[1])
            )
            if key == '3':
                return bounds

            img_array = _ScreenShotCapturer.capture(bounds=bounds)
            Cv2Visualizer.show(img_array=img_array,
                               continue_program=False)


class _KeyPressCapturer:

    def __init__(self, acceptable_keys: set):
        self._acceptable_keys = acceptable_keys

        self._captured_key = None

    def _on_press(self, key):
        try:
            key = key.char
        except AttributeError:
            key = key

        if key in self._acceptable_keys:
            print(f"\tDetected acceptable key press for {key}")
            self._captured_key = key
            return False

        return True

    def capture(self) -> str | keyboard.Key:
        print(f"\tListening for key press...")
        self._captured_key = None

        listener = keyboard.Listener(on_press=self._on_press)
        listener.start()

        while self._captured_key is None:
            time.sleep(0.05)

        listener.stop()
        return self._captured_key


class UiImage:

    def __init__(self,
                 ui_element: UiElement,
                 img_array: np.ndarray,
                 id_: uuid.UUID = None):
        self.ui_element = ui_element
        self.img_array = img_array
        self.id_ = id_ or uuid.uuid4().hex


class UiTableRow:

    def __init__(self,
                 ui_element: UiElement,
                 ratio_img: UiImage,
                 stock_img: UiImage,
                 row_idx: int,
                 id_: uuid.UUID = None):
        self.ui_element = ui_element
        self.ratio_img = ratio_img
        self.stock_img = stock_img
        self.row_idx = row_idx
        self.id_ = id_

    def to_dict(self) -> dict:
        d = self.__dict__.copy()
        return d


class _ScreenShotCapturer:

    @staticmethod
    def capture(bounds: CaptureBounds) -> np.ndarray:
        import mss
        with mss.mss() as sct:
            region = {
                "left": bounds.x_min,
                "top": bounds.y_min,
                "width": bounds.width,
                "height": bounds.height
            }
            img_array = np.array(sct.grab(region))

            return img_array


class ScreenBoundsManager:

    def __init__(self, capture_bounds: dict[UiElement, CaptureBounds | CaptureTableBounds] = None):
        self._bounds = capture_bounds or dict()

    @property
    def filled(self):
        self_ui_elements = set(self._bounds.keys())
        all_ui_elements = {e for e in UiElement}
        return bool(all_ui_elements - self_ui_elements)

    def to_dict(self) -> dict:
        d = {'_bounds': {k: v.to_dict() for k, v in self._bounds.items()}}
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "ScreenBoundsManager":
        if not d:
            return ScreenBoundsManager()

        capture_bounds = {UiElement(ui_element): CaptureBounds.from_dict(d) for ui_element, d in d['_bounds'].items()}
        return ScreenBoundsManager(capture_bounds)

    @property
    def all_bounds(self) -> list[CaptureBounds]:
        """

        :return: All CaptureBounds stored in this class. Note that this does not break CaptureTableBounds into rows.
        """
        return list(self._bounds.values())

    def add_bounds(self, ui_element: UiElement, bounds: CaptureBounds | CaptureTableBounds):
        if ui_element in self._bounds:
            logger.warning(f"Bounds for UiElement {ui_element.value} already exists. Overwriting...")

        self._bounds[ui_element] = bounds

    def fetch_bounds(self, ui_element: UiElement) -> CaptureBounds | CaptureTableBounds:
        return self._bounds[ui_element]


class UiBoundsCreator:

    _whole_screen_bounds = CaptureBounds(
        x_min=0,
        y_min=0,
        x_max=5119,
        y_max=1439
    )

    _table_ui_elements = {UiElement.AVAILABLE_TRADES, UiElement.COMPETING_TRADES, UiElement.TRADES_SOLO_TABLE}

    @classmethod
    def _create_relative_bounds(cls) -> dict[UiElement, RelativeBounds]:
        bounds = dict()
        bounds[UiElement.AVAILABLE_TRADES] = RelativeBounds(
            pct_width=0.255,
            pct_height=0.17,
            pct_from_x_min=0.37,
            pct_from_y_min=0.166
        )
        bounds[UiElement.TRADES_SOLO_TABLE] = RelativeBounds(
            pct_width=0.255,
            pct_height=0.17,
            pct_from_x_min=0.37,
            pct_from_y_min=0.135
        )
        bounds[UiElement.COMPETING_TRADES] = RelativeBounds(
            pct_width=0.255,
            pct_height=0.17,
            pct_from_x_min=0.37,
            pct_from_y_min=0.401
        )
        return bounds

    @classmethod
    def _convert_relative_to_absolute_bound(cls,
                                            parent_bounds: CaptureBounds,
                                            relative_bounds: RelativeBounds) -> CaptureBounds:
        parent_width = parent_bounds.x_max - parent_bounds.x_min
        parent_height = parent_bounds.y_max - parent_bounds.y_min

        x_min = int(parent_bounds.x_min + (parent_width * relative_bounds.pct_from_x_min))
        y_min = int(parent_bounds.y_min + (parent_height * relative_bounds.pct_from_y_min))
        x_max = int(x_min + (relative_bounds.pct_width * parent_width))
        y_max = int(y_min + (relative_bounds.pct_height * parent_height))

        return CaptureBounds(
            x_min=x_min,
            y_min=y_min,
            x_max=x_max,
            y_max=y_max
        )

    @classmethod
    def create_bounds(cls, show: bool = False) -> ScreenBoundsManager:
        print("Capture the entire currency exchange screen.")
        ui_bounds = _ScreenBoundsCapturer().capture()

        relative_bounds_d = cls._create_relative_bounds()

        bounds_manager = ScreenBoundsManager()
        for ui_element, relative_bounds in relative_bounds_d.items():
            bounds = cls._convert_relative_to_absolute_bound(parent_bounds=ui_bounds,
                                                             relative_bounds=relative_bounds)
            if ui_element in cls._table_ui_elements:
                bounds = CaptureTableBounds(
                    x_min=bounds.x_min,
                    y_min=bounds.y_min,
                    x_max=bounds.x_max,
                    y_max=bounds.y_max
                )

            bounds_manager.add_bounds(ui_element=ui_element, bounds=bounds)

        if show:
            img_array = _ScreenShotCapturer.capture(cls._whole_screen_bounds)
            for bounds in bounds_manager.all_bounds:
                Cv2Visualizer.draw_rectangle(
                    img_array=img_array,
                    x=bounds.x_min,
                    y=bounds.y_min,
                    w=bounds.x_max - bounds.x_min,
                    h=bounds.y_max - bounds.y_min,
                    color='blue',
                    inplace=True
                )
            Cv2Visualizer.show(img_array,
                               continue_program=True)

        return bounds_manager

class MarketImageCollection:

    def __init__(self,
                 want_currency: Currency,
                 have_currency: Currency    ,
                 date_taken: datetime.datetime,
                 id_: str = None,
                 available_currency_ui_rows: list[UiTableRow] = None,
                 competing_currency_ui_rows: list[UiTableRow] = None):
        self.want_currency = want_currency
        self.have_currency = have_currency
        self.date_taken = date_taken

        self.id_ = id_ or uuid.uuid4().hex
        self.available_currency_ui_rows = available_currency_ui_rows
        self.competing_currency_ui_rows = competing_currency_ui_rows

    @property
    def all_images(self) -> list[UiImage]:
        available_images = [
            img
            for row in self.available_currency_ui_rows
            for img in [row.ratio_img, row.stock_img]
        ]
        competing_images = [
            img
            for row in self.competing_currency_ui_rows
            for img in [row.ratio_img, row.stock_img]
        ]
        return available_images + competing_images


class ScreenShotsCoordinator:

    _ratio_supply_ui_elements = [
        UiElement.AVAILABLE_TRADES,
        UiElement.COMPETING_TRADES
    ]

    def __init__(self,
                 screen_bounds_manager: ScreenBoundsManager):
        self.bounds_manager = screen_bounds_manager

    def _create_ui_table_rows(self, solo_table: bool, available_or_competing: UiElement) -> list[UiTableRow]:
        if solo_table:
            bounds = self.bounds_manager.fetch_bounds(UiElement.TRADES_SOLO_TABLE)
        else:
            bounds = self.bounds_manager.fetch_bounds(available_or_competing)

        if not isinstance(bounds, CaptureTableBounds):
            raise TypeError(f'Expected CaptureTableBounds but received {type(bounds)}')

        table_rows = []
        for i, (ratio_bounds, stock_bounds) in enumerate(zip(bounds.ratio_bounds, bounds.stock_bounds)):
            ratio_img_array = _ScreenShotCapturer.capture(ratio_bounds)
            ratio_img = UiImage(ui_element=available_or_competing,
                                img_array=ratio_img_array)
            stock_img_array = _ScreenShotCapturer.capture(stock_bounds)
            stock_img = UiImage(ui_element=available_or_competing,
                                img_array=stock_img_array)
            table_rows.append(UiTableRow(
                ui_element=available_or_competing,
                ratio_img=ratio_img,
                stock_img=stock_img,
                row_idx=i
            ))

        return table_rows


    def _capture_market_data_images(self,
                                    have_currency: Currency,
                                    want_currency: Currency) -> MarketImageCollection | None:
        ready_to_capture = False
        available_trades_exist = True
        competing_trades_exist = True
        while not ready_to_capture:
            if not available_trades_exist and not competing_trades_exist:
                return MarketImageCollection(want_currency=want_currency,
                                             have_currency=have_currency,
                                             date_taken=datetime.datetime.now())

            key = utils.capture_user_input(
                prompt="Press a key:\n\t1: Ready to capture screen shots\n\t2: Available trades do not exist"
                "\n\t3: Competing trades do not exist\n\t4: Quit capturing",
                valid_inputs={1, 2, 3, 4},
                convert_to=int
            )
            match key:
                case 1:
                    ready_to_capture = True
                case 2:
                    available_trades_exist = False
                case 3:
                    competing_trades_exist = False
                case 4:
                    return None

        print("Press right-click when you want to capture screen shots")
        utils.wait_for_right_click()

        available_imgs = None
        competing_imgs = None
        if available_trades_exist and not competing_trades_exist:
            available_imgs = self._create_ui_table_rows(solo_table=True,
                                                        available_or_competing=UiElement.AVAILABLE_TRADES)
        elif not available_trades_exist and competing_trades_exist:
            competing_imgs = self._create_ui_table_rows(solo_table=True,
                                                        available_or_competing=UiElement.COMPETING_TRADES)
        elif available_trades_exist and competing_trades_exist:
            available_imgs = self._create_ui_table_rows(solo_table=False,
                                                        available_or_competing=UiElement.AVAILABLE_TRADES)
            competing_imgs = self._create_ui_table_rows(solo_table=False,
                                                        available_or_competing=UiElement.COMPETING_TRADES)

        return MarketImageCollection(have_currency=have_currency,
                                     want_currency=want_currency,
                                     date_taken=datetime.datetime.now(),
                                     available_currency_ui_rows=available_imgs,
                                     competing_currency_ui_rows=competing_imgs)

    def capture_screen_shots(self,
                             currency_pairs_to_capture: set[tuple[Currency, Currency]],
                             show: bool = False) -> Iterable[MarketImageCollection]:
        ordered_pairs = sorted(list(currency_pairs_to_capture), key=lambda p: (p[1].value, p[0].value))
        for currency_pair in ordered_pairs:
            have_currency = currency_pair[0]
            want_currency = currency_pair[1]
            print(f"\n\n---\nCapture market data screen shots for:\nWant: {want_currency.value}"
                  f"\nHave: {have_currency.value}\n---")
            market_images = self._capture_market_data_images(have_currency=have_currency,
                                                             want_currency=want_currency)

            if not market_images:
                return

            if show:
                for img in market_images.all_images:
                    Cv2Visualizer.show(img_array=img.img_array,
                                       continue_program=True)

            yield market_images
