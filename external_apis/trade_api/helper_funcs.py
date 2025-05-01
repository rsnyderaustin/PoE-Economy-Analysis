
import re


def parse_values_from_mod_text(mod_text: str) -> tuple:
    numbers = tuple(map(int, re.findall(r'\b\d+\b', mod_text)))
    return numbers


def replace_mod_text_values(mod_text: str, replacement_values):
    replacement_values = [str(value) for value in replacement_values]

    def repl_function(match):
        return replacement_values.pop(0)

    new_string = re.sub(r'\d+', string=mod_text, repl=repl_function)
    return new_string
