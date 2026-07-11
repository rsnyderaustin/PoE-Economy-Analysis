from dataclasses import dataclass
from typing import NamedTuple, Optional

@dataclass
class Range(NamedTuple):
    min: int | float
    max: int | float

    def __str__(self):
        return f"{self.min}..{self.max}"

    @property
    def values_count(self) -> int:
        return self.max + 1 - self.min

    @property
    def is_point(self) -> bool:
        return self.min == self.max

    @property
    def query_value(self):
        return {
            'min': self.min,
            'max': self.max
        }

class RangeService:

    @classmethod
    def split(cls, r: Range, number_of_parts: int) -> list["Range"]:
        if r.min == r.max:
            return [r]

        values_count = r.max + 1 - r.min

        # We need to have at least one for a step value
        iterative_value = max(round(values_count / number_of_parts), 1) - 1

        ranges = []
        for i in range(number_of_parts):
            # Calculate the start and end for this specific step
            part_min = r.min + (i * (iterative_value + 1))
            part_max = part_min + iterative_value

            # Stop if the start is already past the limit
            if part_min > r.max:
                break

            # Cap the max at self.max
            ranges.append(Range(min=part_min, max=min(part_max, r.max)))

        ranges[-1].max = r.max

        return ranges

@dataclass
class ListIndex:
    index: int


@dataclass
class DictKey:
    key: str
