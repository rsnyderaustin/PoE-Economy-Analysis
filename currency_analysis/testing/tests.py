from pathlib import Path

import sys
print(sys.executable)
print(sys.version)

import cv2
import logging

from currency_analysis.market_data_capture import (
    _MarketDataCaptureManager, _ScreenShotCapturer, _ScreenBoundsCapturer, _MarketUiElement,
    _ScreenShotAnalyzer, _ScreenShot
)

logging.basicConfig(level=logging.INFO)

def test_build_supply_table():
    # bounds = _ScreenBoundsCapturer(ui_element=_MarketUiElement.AVAILABLE_TRADES).capture()
    # table_screen_shot = _ScreenShotCapturer().capture(bounds=bounds)
    img_path = Path(__file__).resolve().parent / "available-trades.png"
    img_array = cv2.imread(str(img_path))
    supply_table = _ScreenShotAnalyzer(logger=logging.getLogger('testing')).analyze_for_table(
        img_array=img_array,
        have_currency='Divination Scarab of Pilfering',
        want_currency='Chaos Orb'
    )

def test_run():
    manager = _MarketDataCaptureManager(logger=logging.getLogger('testing'))
    manager.capture()

test_build_supply_table()

