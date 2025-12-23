import logging
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


ui_element_enums = set(e for e in CurrencyExchangeUiElement)


@dataclass(frozen=True)
class _CaptureBounds:
    ui_element: CurrencyExchangeUiElement
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


class ScreenBoundsCapturer:

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

    def capture(self, ui_element: CurrencyExchangeUiElement) -> _CaptureBounds:
        from pynput import mouse

        with mouse.Listener(on_click=self._on_click) as listener:
            print("Click to select the top left capture corner")
            listener.join()

        with mouse.Listener(on_click=self._on_click) as listener:
            print(f"Click to select the bottom right capture corner")
            listener.join()

        print(f"1: Take a sample screen shot\n2: Continue")
        key = _KeyPressCapturer(acceptable_keys={'1', '2'}).capture()

        bounds = _CaptureBounds(
            ui_element=ui_element,
            x_min=min(self._click_point_start[0], self._click_point_end[0]),
            y_min=min(self._click_point_start[1], self._click_point_end[1]),
            x_max=max(self._click_point_start[0], self._click_point_end[0]),
            y_max=max(self._click_point_start[1], self._click_point_end[1])
        )
        if key == '2':
            return bounds

        screen_shot = _ScreenShotCapturer.capture(bounds=bounds)
        Cv2Visualizer.show(img_array=screen_shot.img_array)

        print(f"1: Recapture bounds\n2: Continue")
        key = _KeyPressCapturer(acceptable_keys={'1', '2'}).capture()

        if key == '1':
            return self.capture(ui_element=ui_element)

        return bounds


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
            print(f"\tDetected acceptable key press for {key.char}")
            self._captured_key = key
            return False

    def capture(self) -> str | keyboard.Key:
        print(f"\tListening for key press...")
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


class _ScreenBoundsManager:

    def __init__(self,
                 logger: logging.Logger):
        self._bounds = dict()
        self._logger = logger

    @property
    def captured_ui_elements(self) -> list[CurrencyExchangeUiElement]:
        return list(self._bounds.keys())

    def add_bounds(self, ui_element: CurrencyExchangeUiElement, bounds: _CaptureBounds):
        if ui_element in self._bounds:
            self._logger.warning(f"Bounds {ui_element} already exists. Overwriting...")

        self._bounds[ui_element] = bounds

    def fetch_bounds(self, ui_element: CurrencyExchangeUiElement) -> _CaptureBounds | None:
        return self._bounds.get(ui_element, None)


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


class ScreenShotCaptureInterface:

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

    def __init__(self, logger: logging.Logger):
        self._logger = logger

        self._bounds_m = _ScreenBoundsManager(logger=self._logger)

    def capture_bounds(self, ui_elements: list[CurrencyExchangeUiElement]):
        print(f"\nCaptured UI elements thus far: {self._bounds_m.captured_ui_elements}")

        options_d = {i: ui_element for i, ui_element in enumerate(ui_elements)}
        acceptable_keys = {str(k) for k in options_d.keys()}
        acceptable_keys.add(keyboard.Key.backspace)
        key_capturer = _KeyPressCapturer(acceptable_keys=acceptable_keys)

        done = False
        while not done:
            print(f"\nPress a number to capture the associated UI element:")
            pprint.pprint(options_d)
            print(f"Or press 'Backspace' to quit")

            key = key_capturer.capture()

            if key == keyboard.Key.backspace:
                break

            ui_element = options_d[int(key)]

            bounds = ScreenBoundsCapturer().capture(ui_element)
            self._bounds_m.add_bounds(ui_element=ui_element,
                                      bounds=bounds)

    def capture_screen_shots(self):
        while True:
            print(f"Press 'f' to finish or 't' to capture screen shots for {self.__class__._screen_shot_group_1}")
            key = _KeyPressCapturer(acceptable_keys={'f', 't'}).capture()
            if key == 'f':
                return

            collection = ScreenShotCollection()
            for e in self.__class__._screen_shot_group_1:
                bounds = self._bounds_m.fetch_bounds(ui_element=e)

                screen_shot = _ScreenShotCapturer.capture(bounds)
                collection.add_screen_shot(ui_element=e,
                                           screen_shot=screen_shot)

            print(f"Press 't' to capture screen shots for {self.__class__._screen_shot_group_2}")
            for e in self.__class__._screen_shot_group_2:
                bounds = self._bounds_m.fetch_bounds(ui_element=e)

                screen_shot = _ScreenShotCapturer.capture(bounds)
                collection.add_screen_shot(ui_element=e,
                                           screen_shot=screen_shot)

            yield collection
