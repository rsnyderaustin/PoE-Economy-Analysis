import re

import numpy as np


class TextAnalyzer:

    _neg_float_p = r'-?\d+(?:\.\d+)?'
    _numbers_capture_pattern = rf'{_neg_float_p} to {_neg_float_p} | {_neg_float_p} | {_neg_float_p}-{_neg_float_p}'

    @classmethod
    def _singular_number_convert(cls, s: str):
        return float(s) if '.' in s else int(s)

    @classmethod
    def _replace_numbers(cls, match):
        if ' to ' in match.group():
            return '# to #'
        elif '-' in match.group():
            return '#-#'
        else:
            return '#'

    @classmethod
    def extract_numbers_from_string(cls, s: str) -> tuple[list[int | float], str]:
        """
            :return A tuple containing the extracted numbers from the string, and the original string with
                numbers replaced with #
        """
        vals = []
        for match in re.finditer(cls._numbers_capture_pattern, s):
            if ' to ' in match.group() or '-' in match.group():
                val = np.mean([cls._singular_number_convert(g) for g in match.groups()])
            else:
                val = cls._singular_number_convert(match.groups()[0])

            vals.append(val)
        formatted_s = re.sub(cls._numbers_capture_pattern, cls._replace_numbers, s)
        return vals, formatted_s

