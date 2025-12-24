import logging
logger = logging.getLogger(__name__)
import pprint
import time
from dataclasses import dataclass
from enum import Enum

import numpy as np
from pynput import keyboard

from currency_analysis.visualizing import Cv2Visualizer


class CurrencyExchangeUiElement(Enum):
    WANT_CURRENCY = 'Want Currency'
    WANT_CURRENCY_AMOUNT = 'Want Currency Amount'
    HAVE_CURRENCY = 'Have Currency'
    GOLD_COST = 'Gold Cost'
    AVAILABLE_TRADES = 'Available Trades'
    COMPETING_TRADES = 'Competing Trades'


@dataclass(frozen=True)
class _RelativeBounds:
    ui_element: CurrencyExchangeUiElement
    width: float
    height: float
    from_x_min: float
    from_y_min: float


@dataclass(frozen=True)
class _CaptureBounds:
    x_min: int
    y_min: int
    x_max: int
    y_max: int

    def to_dict(self) -> dict:
        d = self.__dict__
        d['ui_element'] = d['ui_element'].value
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "_CaptureBounds":
        d['ui_element'] = CurrencyExchangeUiElement(d['ui_element'])
        return _CaptureBounds(**d)

    @property
    def height(self) -> int:
        return int(self.y_max - self.y_min)

    @property
    def width(self) -> int:
        return int(self.x_max - self.x_min)


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

    def capture(self) -> _CaptureBounds:
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

            bounds = _CaptureBounds(
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


@dataclass(frozen=True)
class ScreenShot:
    img_array: np.ndarray
    x_min: int
    y_min: int
    x_max: int
    y_max: int


class _ScreenShotCapturer:

    @staticmethod
    def capture(bounds: _CaptureBounds) -> ScreenShot:
        import mss
        with mss.mss() as sct:
            region = {
                "left": bounds.x_min,
                "top": bounds.y_min,
                "width": bounds.width,
                "height": bounds.height
            }
            img = np.array(sct.grab(region))

            return ScreenShot(
                img_array=img,
                x_min=bounds.x_min,
                y_min=bounds.y_min,
                x_max=bounds.x_max,
                y_max=bounds.y_max
            )


class _UiElementBoundsDeterminer:

    relative_bounds = [
        RelativeBounds(
            width=
    )
    ]

    def create_bounds_from_parent(self, parent_bounds: _CaptureBounds) -> _CaptureBounds:
        return


class ScreenBoundsManager:

    def __init__(self, capture_bounds: list[_CaptureBounds] = None):
        self._bounds = {cb.ui_element: cb for cb in capture_bounds} if capture_bounds else dict()

    @property
    def filled(self):
        self_ui_elements = set(self._bounds.keys())
        all_ui_elements = {e for e in CurrencyExchangeUiElement}
        return bool(all_ui_elements - self_ui_elements)

    def to_dict(self) -> dict:
        d = {'_bounds': [v.to_dict() for k, v in self._bounds.items()]}
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "ScreenBoundsManager":
        if not d:
            return ScreenBoundsManager()

        capture_bounds = [_CaptureBounds.from_dict(d) for d in d['_bounds']]
        return ScreenBoundsManager(capture_bounds)

    def add_bounds(self, ui_element: CurrencyExchangeUiElement, bounds: _CaptureBounds):
        if ui_element in self._bounds:
            logger.warning(f"Bounds {ui_element} already exists. Overwriting...")

        self._bounds[ui_element] = bounds

    def fetch_bounds(self, ui_element: CurrencyExchangeUiElement) -> _CaptureBounds | None:
        return self._bounds.get(ui_element, None)


class ScreenBoundsCoordinator:

    def __init__(self, screen_bounds_manager: ScreenBoundsManager = None):
        self._screen_bounds_manager = screen_bounds_manager

    def determine_ui_element_bounds(self) -> ScreenBoundsManager:
        if self._screen_bounds_manager.filled:
            return self._screen_bounds_manager

        print("Capture Currency Exchange panel bounds")
        ui_bounds = _ScreenBoundsCapturer().capture()



class ScreenShotCollection:

    def __init__(self):
        self._screen_shots = dict()

    def add_screen_shot(self, ui_element: CurrencyExchangeUiElement, screen_shot: ScreenShot):
        if ui_element in self._screen_shots:
            print(f"Warning: screen shot for {ui_element} already exists. Overwriting...")

        self._screen_shots[ui_element] = screen_shot

    def fetch_screen_shot(self, ui_element: CurrencyExchangeUiElement) -> ScreenShot:
        if ui_element not in self._screen_shots:
            raise ValueError(f"UiElement {ui_element} ScreenShot not in self._screen_shots")

        return self._screen_shots[ui_element]

    def has_screen_shot(self, ui_element: CurrencyExchangeUiElement) -> bool:
        return ui_element in self._screen_shots


class ScreenShotsCoordinator:

    _screen_shot_group_1 = [
        CurrencyExchangeUiElement.WANT_CURRENCY,
        CurrencyExchangeUiElement.HAVE_CURRENCY,
        CurrencyExchangeUiElement.AVAILABLE_TRADES,
        CurrencyExchangeUiElement.COMPETING_TRADES
    ]
    _screen_shot_group_2 = [
        CurrencyExchangeUiElement.WANT_CURRENCY_AMOUNT,
        CurrencyExchangeUiElement.GOLD_COST
    ]

    def __init__(self,
                 screen_bounds_manager: ScreenBoundsManager):
        self.bounds_manager = screen_bounds_manager

    def capture_screen_shots(self):
        while True:
            print(f"Press 't' to capture screen shots for {[e.value for e in self.__class__._screen_shot_group_1]}"
                  f"\nOr press 'Backspace' to quit capturing")
            key = _KeyPressCapturer(acceptable_keys={keyboard.Key.backspace, 't'}).capture()
            if key == keyboard.Key.backspace:
                return

            collection = ScreenShotCollection()
            for e in self.__class__._screen_shot_group_1:
                bounds = self.bounds_manager.fetch_bounds(ui_element=e)

                screen_shot = _ScreenShotCapturer.capture(bounds)
                collection.add_screen_shot(ui_element=e,
                                           screen_shot=screen_shot)

            print(f"Press 't' to capture screen shots for {[e.value for e in self.__class__._screen_shot_group_2]}"
                  f"\nOR 'Backspace' to quit capturing")
            key = _KeyPressCapturer(acceptable_keys={keyboard.Key.backspace, 't'}).capture()
            if key == keyboard.Key.backspace:
                return

            for e in self.__class__._screen_shot_group_2:
                bounds = self.bounds_manager.fetch_bounds(ui_element=e)

                screen_shot = _ScreenShotCapturer.capture(bounds)
                collection.add_screen_shot(ui_element=e,
                                           screen_shot=screen_shot)

            yield collection
