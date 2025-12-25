import datetime
import logging
import uuid

from currency_analysis.data_objects import Currency

logger = logging.getLogger(__name__)
import time
from dataclasses import dataclass
from enum import Enum

import numpy as np
from pynput import keyboard

from currency_analysis.visualizing import Cv2Visualizer


class UiElement(Enum):
    WANT_CURRENCY_AMOUNT = 'Want Currency Amount'
    GOLD_COST = 'Gold Cost'
    AVAILABLE_TRADES = 'Available Trades'
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
        d = self.__dict__
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
        self.x_min = x_min
        self.y_min = y_min
        self.x_max = x_max
        self.y_max = y_max

        self.num_rows = num_rows

    def split_into_row_bounds(self) -> list[CaptureBounds]:
        row_boundaries = np.linspace(
            self.y_min,
            self.y_max,
            self.num_rows + 1,
            dtype=int
        )

        row_slices = [(row_boundaries[i], row_boundaries[i + 1])
                      for i in range(self.num_rows)]

        return [
            CaptureBounds(
                x_min=self.x_min,
                y_min=row_slice[0],
                x_max=self.x_max,
                y_max=row_slice[1]
            )
            for row_slice in row_slices
        ]


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
            print(f"1: Take a sample screen shot\n2: Recapture bounds\n3: Continue")
            key = _KeyPressCapturer(acceptable_keys={'1', '2', '3'}).capture()

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

            screen_shot = _ScreenShotCapturer.capture(bounds=bounds)
            Cv2Visualizer.show(img_array=screen_shot.img_array)


class _KeyPressCapturer:

    def __init__(self, acceptable_keys: set):
        self._acceptable_keys = acceptable_keys

        self._captured_key = None

    def _on_press(self, key):
        try:
            key = key.char
        except AttributeError:
            pass

        if key in self._acceptable_keys:
            print(f"\tDetected acceptable key press for {key}")
            self._captured_key = key
            return False

    def capture(self) -> str | keyboard.Key:
        print(f"\tListening for key press...")
        self._captured_key = None

        listener = keyboard.Listener(on_press=self._on_press)
        listener.start()

        while self._captured_key is None:
            time.sleep(0.1)

        listener.stop()

        return self._captured_key


class Image:

    def __init__(self,
                 img_array: np.ndarray,
                 id_: uuid.UUID = None):
        self.img_array = img_array
        self.id_ = id_ or uuid.uuid4().hex


class RowImage(Image):

    def __init__(self, img_array: np.ndarray, row_idx: int, id_: uuid.UUID = None):
        super().__init__(img_array, id_)
        self.row_idx = row_idx


class _ScreenShotCapturer:

    @staticmethod
    def capture(bounds: CaptureBounds) -> Image:
        import mss
        with mss.mss() as sct:
            region = {
                "left": bounds.x_min,
                "top": bounds.y_min,
                "width": bounds.width,
                "height": bounds.height
            }
            img = np.array(sct.grab(region))

            return Image(img_array=img)


class ScreenBoundsManager:

    def __init__(self, capture_bounds: dict[UiElement: CaptureBounds | CaptureTableBounds] = None):
        self._bounds = capture_bounds or dict()

    @property
    def filled(self):
        self_ui_elements = set(self._bounds.keys())
        all_ui_elements = {e for e in UiElement}
        return bool(all_ui_elements - self_ui_elements)

    def to_dict(self) -> dict:
        d = {'_bounds': [v.to_dict() for k, v in self._bounds.items()]}
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "ScreenBoundsManager":
        if not d:
            return ScreenBoundsManager()

        capture_bounds = [CaptureBounds.from_dict(d) for d in d['_bounds']]
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

    _table_ui_elements = {UiElement.AVAILABLE_TRADES, UiElement.COMPETING_TRADES}

    @classmethod
    def _create_relative_bounds(cls) -> dict[UiElement: RelativeBounds]:
        bounds = dict()
        bounds[UiElement.WANT_CURRENCY_AMOUNT] = RelativeBounds(
            pct_width=0.095,
            pct_height=0.028,
            pct_from_x_min=0.335,
            pct_from_y_min=0.13
        )
        bounds[UiElement.GOLD_COST] = RelativeBounds(
            pct_width=0.075,
            pct_height=0.025,
            pct_from_x_min=0.492,
            pct_from_y_min=0.19
        )
        bounds[UiElement.AVAILABLE_TRADES] = RelativeBounds(
            pct_width=0.255,
            pct_height=0.17,
            pct_from_x_min=0.37,
            pct_from_y_min=0.166
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
            whole_screen_shot = _ScreenShotCapturer.capture(cls._whole_screen_bounds)
            for bounds in bounds_manager.all_bounds:
                Cv2Visualizer.draw_rectangle(
                    img_array=whole_screen_shot.img_array,
                    x=bounds.x_min,
                    y=bounds.y_min,
                    w=bounds.x_max - bounds.x_min,
                    h=bounds.y_max - bounds.y_min,
                    color='blue',
                    inplace=True
                )
            Cv2Visualizer.show(whole_screen_shot.img_array)

        return bounds_manager


class UiImageCollection:

    def __init__(self,
                 have_currency: Currency,
                 want_currency: Currency,
                 date_taken: datetime.datetime,
                 id_: str = None,
                 images: dict[UiElement: list[Image]] = None) -> None:
        self.have_currency = have_currency
        self.want_currency = want_currency
        self.date_taken = date_taken
        self.id_ = id_ or uuid.uuid4().hex
        self.images_d = images or dict()

    @property
    def stored_ui_elements(self) -> list[UiElement]:
        return list(self.images_d.keys())

    def add_images(self, ui_element: UiElement, images: list[Image]):
        if ui_element not in self.images_d:
            self.images_d[ui_element] = []

        self.images_d[ui_element].extend(images)

    def fetch_images(self, ui_element: UiElement) -> list[Image]:
        if ui_element not in self.images_d:
            raise ValueError(f"UiElement {ui_element} image not in self.images_d")

        return self.images_d[ui_element]

    def has_images(self, ui_element: UiElement) -> bool:
        if ui_element not in self.images_d:
            return False

        return len(self.images_d[ui_element]) > 0


class ScreenShotsCoordinator:

    _screen_shot_group_1 = [
        UiElement.WANT_CURRENCY,
        UiElement.HAVE_CURRENCY,
        UiElement.AVAILABLE_TRADES,
        UiElement.COMPETING_TRADES
    ]
    _screen_shot_group_2 = [
        UiElement.WANT_CURRENCY_AMOUNT,
        UiElement.GOLD_COST
    ]

    def __init__(self,
                 screen_bounds_manager: ScreenBoundsManager):
        self.bounds_manager = screen_bounds_manager

    def _prompt_user(self, ui_elements: list[UiElement]):
        print(f"Press 't' to capture screen shots for {[e.value for e in ui_elements]}"
              f"\nOr press 'Backspace' to quit capturing")
        key = _KeyPressCapturer(acceptable_keys={keyboard.Key.backspace, 't'}).capture()
        if key == keyboard.Key.backspace:
            return

    def _capture_and_collect_screen_shot(self,
                                         collection: UiImageCollection,
                                         ui_elements: list[UiElement]):
        for e in ui_elements:
            bounds = self.bounds_manager.fetch_bounds(ui_element=e)

            bounds = bounds.split_into_row_bounds() if isinstance(bounds, CaptureTableBounds) else [bounds]

            screen_shots = [_ScreenShotCapturer.capture(b) for b in bounds]

            collection.add_images(ui_element=e,
                                  images=screen_shots)

    def capture_screen_shots(self, currency_pairs_to_capture: set[tuple[Currency, Currency]]):
        for currency_pair in currency_pairs_to_capture:
            print(f"\n\n--- Capture screen shots for {currency_pair[0]} and {currency_pair[1]} ---")

            collection = UiImageCollection(date_taken=datetime.datetime.now())

            self._prompt_user(ui_elements=self.__class__._screen_shot_group_1)
            self._capture_and_collect_screen_shot(collection=collection,
                                                  ui_elements=self.__class__._screen_shot_group_1)

            self._prompt_user(ui_elements=self.__class__._screen_shot_group_2)
            self._capture_and_collect_screen_shot(collection=collection,
                                                  ui_elements=self.__class__._screen_shot_group_2)

            yield collection
