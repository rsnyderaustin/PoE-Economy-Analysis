
import logging

from currency_analysis.market_data_capture import (
    _MarketDataCaptureManager, _ScreenShotCapturer, _ScreenBoundsCapturer, _MarketUiElement, _ScreenShotAnalyzer
)

logging.basicConfig(level=logging.INFO)

def test_build_supply_table():
    bounds = _ScreenBoundsCapturer(ui_element=_MarketUiElement.AVAILABLE_TRADES).capture()
    table_screen_shot = _ScreenShotCapturer().capture(bounds=bounds)
    supply_table = _ScreenShotAnalyzer(logger=logging.getLogger('testing')).analyze_for_table(
        screen_shot=table_screen_shot,
        have_currency='Divination Scarab of Pilfering',
        want_currency='Chaos Orb'
    )

def test_run():
    manager = _MarketDataCaptureManager(logger=logging.getLogger('testing'))
    manager.capture()

test_build_supply_table()

