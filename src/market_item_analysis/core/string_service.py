import re

import numpy as np


@dataclass
class NumbersExtractedString:
    original_string: str
    pound_substituted_string: str
    numbers: list[int]


class StringService:
    # Regex breakdown:
    # 1. (?P<range_to>...) -> matches "X to Y"
    # 2. (?P<range_hyphen>...) -> matches "X-Y"
    # 3. (?P<single>...) -> matches a lone number
    _num = r'-?\d+(?:\.\d+)?'
    _pattern = re.compile(
        rf'(?P<range_to>{_num}\s+to\s+{_num})|'
        rf'(?P<range_hyphen>{_num}-{_num})|'
        rf'(?P<single>{_num})'
    )

    @classmethod
    def extract_numbers(cls, s: str) -> NumbersExtractedString:
        numbers = []

        def replacer(match: re.Match) -> str:
            if match.group('range_to'):
                nums = [float(n) for n in re.findall(r'-?\d+(?:\.\d+)?', match.group('range_to'))]
                numbers.append(np.mean(nums))
                return "# to #"

            if match.group('range_hyphen'):
                nums = [float(n) for n in re.findall(r'-?\d+(?:\.\d+)?', match.group('range_hyphen'))]
                numbers.append(np.mean(nums))
                return "#-#"

            # Default to single
            numbers.append(float(match.group('single')))
            return "#"

        formatted_string = cls._pattern.sub(replacer, s)

        return NumbersExtractedString(
            original_string=s,
            pound_substituted_string=formatted_string,
            numbers=numbers
        )

