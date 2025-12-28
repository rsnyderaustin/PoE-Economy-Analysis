import re
from functools import wraps

import cv2
import numpy as np

from currency_analysis.data_objects import RatioType, MarketSupplyTable, Currency
from currency_analysis.visualizing import Cv2Visualizer
from currency_analysis import utils


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
    ratio: tuple[float, float] = None
    supply: int = None

class MarketRowProcessor:

    @classmethod
    def _prompt_for_market_row(cls, row_strings: list[str]) -> _MarketRow:
        print(f"Could not determine ratio and stock given row: {row_strings}")
        ratio_str = utils.capture_user_input(prompt="Enter ratio: ",
                                             verification_func=cls._is_valid_ratio)
        ratio = cls.parse_ratio(ratio_str)
        stock = utils.capture_user_input(prompt="Enter stock: ",
                                         convert_to=int)

        market_row = _MarketRow(ratio=ratio,
                                supply=stock)
        return market_row

    @classmethod
    def _is_valid_ratio(cls, raw_ratio: str) -> bool:
        return ':' in raw_ratio and raw_ratio.count(":") == 1

    @classmethod
    def parse_ratio(cls, raw_ratio: str) -> tuple[float, float]:
        raw_ratio = re.sub(r'[<>,]', '', raw_ratio)
        raw_ratio = re.sub(r':+', ':', raw_ratio)

        groups = re.findall(r"([^:]+)", raw_ratio)
        return float(groups[0]), float(groups[1])

    @classmethod
    def create_market_row_from_row_strings(cls, row_strings: list[str]) -> _MarketRow | None:
        if len(row_strings) == 0:
            return _MarketRow()

        if len(row_strings) >= 2 and ':' in row_strings[1]:
            row_strings[0] = ''.join([row_strings[0], row_strings[1]])
            row_strings.pop(1)

        if len(row_strings) == 1:
            first_s = row_strings[0]

            utils.flush_stdin()
            if ':' in first_s:
                stock = utils.capture_user_input(prompt=f"Could not determine stock for ratio {first_s}. Enter here: ",
                                                 convert_to=int)
                row_strings.append(stock)
            else:
                market_row = cls._prompt_for_market_row(row_strings=row_strings)

        try:
            stock = int(row_strings[-1].replace(',', ''))
        except ValueError:
            ratio_str, stock_str = cls._prompt_for_market_row(row_strings=row_strings)
            row_strings = [ratio_str, stock_str]

        if len(row_strings) == 3:
            raw_ratio = f"{row_strings[0]}:{row_strings[1]}"
        else:
            raw_ratio = "".join(row_strings[:-1])

        if not bool(raw_ratio.strip()):
            continue

        is_valid_ratio = cls._is_valid_ratio(raw_ratio)
        while not is_valid_ratio:
            utils.flush_stdin()
            raw_ratio = input(f"Cannot parse raw ratio {raw_ratio}. Type the correct version here:")

            is_valid_ratio = cls._is_valid_ratio(raw_ratio)

        print(f"Parsing raw ratio {raw_ratio}")
        want, have = cls._attempt_to_parse_ratio(raw_ratio)
        print(f"\tParsed into {want}:{have}")


class ScreenShotAnalyzer:
    _SUPPLY_LINE_PATTERN = re.compile(r'^\d+:\d+(?:\.\d+)? \d+$')

    @classmethod
    def correct_table(cls, table: MarketSupplyTable):
        table_rows = len(table.supply_ratios)

        initial_i = utils.capture_user_input(prompt="Corrections?\n\t1: Yes\n\t2: No",
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
                                             valid_inputs=set(range(table_rows)),
                                             convert_to=int)
            row = table_rows[row_i]

            match correction_i:
                case 1:
                    corrected_ratio = utils.capture_user_input(prompt="Enter the corrected ratio: ")
                case 2:
                    corrected_stock = utils.capture_user_input(prompt="Enter the corrected stock: ",
                                                               convert_to=int)

    @classmethod
    def _extract_ratio_from_image(cls, img_array: np.ndarray, show: bool) -> tuple[float, float]:
        row_strings = cls._extract_row_strings(img_array=img_array,
                                               show=show)

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
                             show_steps: bool = False) -> MarketSupplyTable | None:
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

        if ratio_type == RatioType.AVAILABLE:
            table = MarketSupplyTable(have_currency=have_currency,
                                      want_currency=want_currency)
        elif ratio_type == RatioType.COMPETING:
            table = MarketSupplyTable(have_currency=want_currency,
                                      want_currency=have_currency)
        else:
            raise NotImplementedError

        for row_array in img_arrays:
            """for thresh in range(80, 120):
                s = (
                    _ImageProcessor(row_array,
                                    logger=logger)
                    .grayscale()
                    .show(skip=not show_steps)
                    .isolate_outlines()
                    .show(skip=not show_steps)
                    .resize(new_size=600)
                    .show(skip=not show_steps)
                    .to_string(allowed_chars='0123456789:,.<>')
                )"""
            row_strings = (
                ImageProcessor(row_array)
                .grayscale()
                .isolate_outlines(white_threshold=120)
                .resize(new_size=600)
                .show(skip=not show_steps)
                .to_strings(allowed_chars='0123456789:,.<>')
            )

            if ratio_type == RatioType.COMPETING:
                want, have = have, want
                raw_ratio = f"{have}:{want}"

            table.add_ratio_supply(raw_ratio=raw_ratio,
                                   want_per_have=want/have,
                                   want_supply=stock)

        print("Extracted supply table:")
        table.print()
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

