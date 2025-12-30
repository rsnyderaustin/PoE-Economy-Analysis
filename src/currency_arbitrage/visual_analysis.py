import re
from functools import wraps

import cv2
import numpy as np

from src.currency_arbitrage.data_objects import RatioType, MarketSupplyTable, Currency
from src.currency_arbitrage.visualizing import Cv2Visualizer
from src.currency_arbitrage import utils


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


class ImageProcessor:

    def __init__(self, img_array: np.ndarray):
        self._img_array = img_array

    @property
    def img_array(self):
        return self._img_array

    @skippable
    def show(self,
             name: str = "Image",
             skip: bool = False) -> "ImageProcessor":
        Cv2Visualizer.show(self._img_array,
                           name=name)

        return self

    @skippable
    def to_color(self,
                 skip: bool = False) -> "ImageProcessor":
        self._img_array = cv2.cvtColor(self._img_array,
                                       cv2.COLOR_GRAY2BGR)

        return self

    @skippable
    def grayscale(self,
                  skip: bool = False) -> "ImageProcessor":
        self._img_array = cv2.cvtColor(self._img_array, cv2.COLOR_BGR2GRAY)
        return self

    @skippable
    def invert_black_white(self,
                           skip: bool = False) -> "ImageProcessor":
        self._img_array = cv2.bitwise_not(self._img_array)

        return self

    @skippable
    def apply_clahe(self,
                    clip_limit: float = 2.0,
                    tile_size: tuple[int, int] = (8, 8),
                    skip: bool = False) -> "ImageProcessor":
        clahe = cv2.createCLAHE(clipLimit=clip_limit,
                                tileGridSize=tile_size)
        self._img_array = clahe.apply(self._img_array)

        return self

    @skippable
    def close_gaps(self,
                   grid_size: tuple[int, int] = (2, 2),
                   closure_iterations: int = 1,
                   skip: bool = False) -> "ImageProcessor":
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
                 skip: bool = False) -> "ImageProcessor":
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
               skip: bool = False) -> "ImageProcessor":
        kernel = np.ones(brush_size, np.uint8)
        self._img_array = cv2.dilate(self._img_array,
                                     kernel,
                                     iterations=iterations)

        return self

    @skippable
    def isolate_outlines(self,
                         white_threshold: int | None = 120) -> "ImageProcessor":
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
               skip: bool = False) -> "ImageProcessor":
        shape = self._img_array.shape

        if len(shape) == 2:  # grayscale
            curr_height, curr_width = shape
        elif len(shape) == 3:  # color
            curr_height, curr_width = shape[:2]
        else:
            raise ValueError(f"Invalid img array shape: {shape}")

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


class _MarketRow:
    ratio: tuple[float, float] | None = None
    supply: int | None = None

class MarketRowProcessor:

    @classmethod
    def _prompt_for_market_row(cls, row_strings: list[str]) -> _MarketRow:
        print(f"Could not determine ratio and stock given row: {row_strings}")
        ratio_str = utils.capture_user_input(prompt="Enter ratio: ",
                                             verification_func=cls.is_valid_ratio)
        ratio = cls.parse_ratio(ratio_str)
        stock = utils.capture_user_input(prompt="Enter stock: ",
                                         convert_to=int)

        market_row = _MarketRow(ratio=ratio,
                                supply=stock)
        return market_row

    @classmethod
    def is_valid_ratio(cls, raw_ratio: str) -> bool:
        return ':' in raw_ratio and raw_ratio.count(":") == 1

    @classmethod
    def parse_ratio(cls, raw_ratio: str) -> tuple[float, float] | None:
        raw_ratio = re.sub(r'[<>,]', '', raw_ratio)
        raw_ratio = re.sub(r':+', ':', raw_ratio)

        groups = re.findall(r"([^:]+)", raw_ratio)

        if len(groups) != 2:
            return None

        want, have = float(groups[0]), float(groups[1])

        if want != 1.0 and have != 1.0:
            return None

        return want, have


class ScreenShotAnalyzer:
    _SUPPLY_LINE_PATTERN = re.compile(r'^\d+:\d+(?:\.\d+)? \d+$')

    @classmethod
    def prompt_to_correct_table(cls, table: MarketSupplyTable):
        num_table_rows = len(table.ratio_supplies)

        initial_i = utils.capture_user_input(prompt="Corrections?\n\t1: Yes\n\t2: No\n ",
                                             valid_inputs={1, 2},
                                             convert_to=int)
        if initial_i == 2:
            return

        while True:
            correction_i = utils.capture_user_input(prompt="\n\nSelect correction option:\n\t1: Ratio\n\t2: Stock\n\t3: Done",
                                                    valid_inputs={1, 2, 3},
                                                    convert_to=int)

            if correction_i == 3:
                return

            row_i = utils.capture_user_input(prompt="Enter the index of the row you'd like to correct: ",
                                             valid_inputs=set(range(num_table_rows)),
                                             convert_to=int)
            row_ratio_supply = table.ratio_supplies[row_i]

            match correction_i:
                case 1:
                    valid_ratio = False
                    while not valid_ratio:
                        corrected_ratio = utils.capture_user_input(prompt="Enter the corrected ratio: ",
                                                                   verification_func=MarketRowProcessor.is_valid_ratio)
                        parse_result = MarketRowProcessor.parse_ratio(corrected_ratio)

                        if not parse_result:
                            continue

                        want, have = parse_result
                        row_ratio_supply.want_per_have = want / have
                        row_ratio_supply.raw_ratio = corrected_ratio
                        valid_ratio = True
                case 2:
                    corrected_stock = utils.capture_user_input(prompt="Enter the corrected stock: ",
                                                               convert_to=int)
                    row_ratio_supply.want_supply = corrected_stock
                    continue

    @classmethod
    def _extract_ratio_from_image(cls, img_array: np.ndarray, show: bool) -> tuple[str, float, float] | None:
        row_strings = cls._extract_row_strings(img_array=img_array,
                                               show=show)

        if not row_strings:
            return None

        collapsed = ''.join(row_strings)
        parsed_ratio = MarketRowProcessor.parse_ratio(collapsed)

        if parsed_ratio:
            want, have = parsed_ratio
        else:
            print(f"Unable to parse ratio from {row_strings}. Displaying...")
            Cv2Visualizer.show(img_array=img_array,
                               continue_program=True)
            raw_ratio = utils.capture_user_input("Enter ratio: ",
                                                 verification_func=MarketRowProcessor.is_valid_ratio)
            want, have = MarketRowProcessor.parse_ratio(raw_ratio)

        return collapsed, want, have

    @classmethod
    def _extract_stock_from_image(cls, img_array: np.ndarray, show: bool) -> int:
        row_strings = cls._extract_row_strings(img_array=img_array,
                                               show=show)

        if len(row_strings) == 1:
            try:
                stock = int(row_strings[0].replace(',', ''))
                return stock
            except ValueError:
                pass

        print("Did not get any strings when analyzing stock image. Displaying image...")
        Cv2Visualizer.show(img_array=img_array,
                           continue_program=True)
        stock = utils.capture_user_input("Enter number: ",
                                         convert_to=int)
        return stock

    @classmethod
    def _extract_row_strings(cls, img_array: np.ndarray, show: bool) -> list[str]:
        preprocessed_img_array = (
            ImageProcessor(img_array=img_array)
            .resize(new_size=600)
            .img_array
        )
        row_strings = (
            ImageProcessor(preprocessed_img_array)
            .grayscale()
            .isolate_outlines(white_threshold=120)
            .resize(new_size=600)
            .show(skip=not show)
            .to_strings(allowed_chars='0123456789:,.<>')
        )
        return row_strings


    @classmethod
    def extract_supply_table(cls,
                             ratio_img_arrays: list[np.ndarray],
                             stock_img_arrays: list[np.ndarray],
                             ratio_type: RatioType,
                             have_currency: Currency,
                             want_currency: Currency,
                             rows_to_extract: int = 6,
                             show_steps: bool = False) -> MarketSupplyTable | None:
        if ratio_type == RatioType.AVAILABLE:
            table = MarketSupplyTable(have_currency=have_currency,
                                      want_currency=want_currency)
        elif ratio_type == RatioType.COMPETING:
            table = MarketSupplyTable(have_currency=want_currency,
                                      want_currency=have_currency)
        else:
            raise NotImplementedError

        if rows_to_extract < 6:
            ratio_img_arrays = ratio_img_arrays[:rows_to_extract]
            stock_img_arrays = stock_img_arrays[:rows_to_extract]

        for ratio_img_array, stock_img_array in zip(ratio_img_arrays, stock_img_arrays):
            extracted_ratio = cls._extract_ratio_from_image(ratio_img_array,
                                                            show=show_steps)
            if not extracted_ratio:
                continue

            raw_ratio_str, want, have = extracted_ratio
            stock = cls._extract_stock_from_image(stock_img_array, show=show_steps)

            if ratio_type == RatioType.COMPETING:
                want, have = have, want
                raw_ratio_str = f"{have}:{want}"

            print(f"Parsed {raw_ratio_str} -> {want}:{have}\tStock: {stock}")
            table.add_ratio_supply(raw_ratio=raw_ratio_str,
                                   want_per_have=want/have,
                                   want_supply=stock)

        print("Extracted supply table:")
        table.print()

        cls.prompt_to_correct_table(table)

        return table

    @classmethod
    def extract_number(cls,
                       img_array: np.ndarray,
                       num_type: type,
                       white_threshold: int = None,
                       show_steps: bool = False):
        strings = (
            ImageProcessor(img_array)
            .grayscale()
            .show(skip=not show_steps)
            .isolate_outlines(white_threshold=white_threshold)
            .show(skip=not show_steps)
            .resize(new_size=600)
            .show(skip=not show_steps)
            .to_strings(allowed_chars='0123456789,')
        )

        if len(strings) == 0:
            print("Did not get any strings when analyzing image. Displaying image...")
            Cv2Visualizer.show(img_array=img_array)
            s = input("Enter number:")
        elif len(strings) == 1:
            s = strings[0]
        else:
            s = input(f"Could not parse gold cost from strings {strings}. Enter it here:")
        s = s.strip().replace(',', '')
        print(f"Extracted {s} from strings {strings}")

        num = num_type(s)
        return num

