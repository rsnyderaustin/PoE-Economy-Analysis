
import re

import inflect

inflect_eng = inflect.engine()


def _convert_to_word(match):
    number = int(match.group())
    return inflect_eng.number_to_words(number).upper()


def create_enum_name(var: str):
    # Replace numbers with words
    cleaned_name = re.sub(r'\d+', _convert_to_word, var)

    # Filter out any non-letters and numbers
    cleaned_name = re.sub(r'[^a-zA-Z0-9\s]', '', cleaned_name)

    cleaned_name = (cleaned_name
                    .upper()
                    .replace(' ', '_')
                    .replace('__', '_')
                    .replace('\n', '_')
                    .replace('-', '_')
                    .lstrip('_')
                    )

