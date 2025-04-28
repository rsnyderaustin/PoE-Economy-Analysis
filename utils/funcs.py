
import re

import inflect

inflect_eng = inflect.engine()


def _convert_to_word(match):
    number = int(match.group())
    return inflect_eng.number_to_words(number).upper()

