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


class ScreenShotAnalyzer:
    _SUPPLY_LINE_PATTERN = re.compile(r'^\d+:\d+(?:\.\d+)? \d+$')

    @classmethod
    def _is_valid_ratio(cls, raw_ratio: str):
        return ':' in raw_ratio and raw_ratio.count(":") == 1

    @classmethod
    def _attempt_to_parse_ratio(cls, raw_ratio: str) -> tuple[float, float]:
        raw_ratio = re.sub(r'[<>,]', '', raw_ratio)
        raw_ratio = re.sub(r':+', ':', raw_ratio)

        is_valid_ratio = cls._is_valid_ratio(raw_ratio)
        while not is_valid_ratio:
            utils.flush_stdin()
            raw_ratio = input(f"Cannot parse raw ratio {raw_ratio}. Type the correct version here:")

            is_valid_ratio = cls._is_valid_ratio(raw_ratio)

        groups = re.findall(r"([^:]+)", raw_ratio)
        return float(groups[0]), float(groups[1])


    @classmethod
    def extract_supply_table(cls,
                             img_arrays: list[np.ndarray],
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
            row_array = (
                ImageProcessor(img_array=row_array)
                .resize(new_size=600)
                .img_array
            )
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
            if len(row_strings) == 0:
                continue
            elif len(row_strings) == 1:
                s = row_strings[0]

                utils.flush_stdin()
                if ':' in s:
                    supply = input(f"Could not determine supply for ratio {s}. Enter here:")
                    row_strings.append(supply)
                else:
                    print(f"Could not determine ratio and supply given row: {s}")
                    ratio_str = input("Enter ratio: ")
                    supply_str = input("Enter supply: ")
                    row_strings = [ratio_str, supply_str]

            if ':' in row_strings[1]:
                row_strings[0] = ''.join([row_strings[0], row_strings[1]])
                row_strings.pop(1)

            supply = int(row_strings[-1].replace(',', ''))

            if len(row_strings) == 3:
                raw_ratio = f"{row_strings[0]}:{row_strings[1]}"
            else:
                raw_ratio = "".join(row_strings[:-1])

            if not bool(raw_ratio.strip()):
                continue

            print(f"Parsing raw ratio {raw_ratio}")
            ratio = cls._attempt_to_parse_ratio(raw_ratio)
            print(f"\tParsed into {ratio}")

            if ratio_type == RatioType.AVAILABLE:
                table.add_ratio_supply(raw_ratio=raw_ratio,
                                       want_per_have=ratio[0]/ratio[1],
                                       want_supply=supply)
            elif ratio_type == RatioType.COMPETING:
                want, have = raw_ratio.split(":", 1)
                flipped = f"{have}:{want}"
                table.add_ratio_supply(raw_ratio=flipped,
                                       want_per_have=ratio[1]/ratio[0],
                                       want_supply=int(supply * ratio[1]))

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

