
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


def remove_piped_brackets(text: str):
    matches = re.findall(r'\[(.*?)\]', text)
    if '[' in text and ']' in text:

        orig_mod_text = text
        # Remove the brackets and take the part after the pipe if it exists
        match = re.search(r'\[([^\]]+)\]', text)
        if match:
            bracket_content = match.group(1)

            # If there is a pipe, split by pipe and take the right side
            if '|' in bracket_content:
                return text.replace('[' + bracket_content + ']', bracket_content.split('|')[1])
            else:
                # If no pipe, just remove the brackets
                return text.replace('[' + bracket_content + ']', bracket_content)

        logging.info(f"Converted {orig_mod_text} to {text}")
        # If no brackets, return the original string
    return text
