
import logging
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


def _process_bracketed_text(match):
    content = match.group(1)

    if '|' in content:
        return content.split('|', 1)[1]

    return content


def remove_piped_brackets(text: str):
    result = re.sub(r'\[(.*?)\]', _process_bracketed_text, text)
    if text != result:
        logging.info(f"Converted {text} to {result}.")
    return result
