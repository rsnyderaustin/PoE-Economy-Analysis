
import logging
import re

from utils.enums import ModClass
from ..things import Rune


def _process_mod_text(mod_text: str):
    if '[' in mod_text and ']' in mod_text:
        # Remove the brackets and take the part after the pipe if it exists
        match = re.search(r'\[([^\]]+)\]', mod_text)
        if match:
            bracket_content = match.group(1)

            # If there is a pipe, split by pipe and take the right side
            if '|' in bracket_content:
                return mod_text.replace('[' + bracket_content + ']', bracket_content.split('|')[1])
            else:
                # If no pipe, just remove the brackets
                return mod_text.replace('[' + bracket_content + ']', bracket_content)

        # If no brackets, return the original string
    return mod_text

class RunesCreator:

    @classmethod
    def create_runes(cls, item_data: dict) -> list[Rune]:
        """
        Because of the limitations around determining mod effects,
        as of right now this function should only be called to fetch and save data internally for rune effects.
        :param item_data:
        :return:
        """
        if ModClass.RUNE.value not in item_data:
            logging.info(f"Requested to create runes when item does not have {ModClass.RUNE.value} attribute."
                         f"\nItem data:\n{item_data}.")
            return []

        # We can only deterministically get rune data when there is one rune socketed, because different types of the same
        # runes can produce one rune text
        if len(item_data['socketedItems']) >= 2:
            logging.info(f"Item has more than one socketer. Skipping.")
            return []

        logging.info("Item only has one socketer. Creating rune.")

        rune_name = item_data['socketedItems'][0]['typeLine']
        rune_mod_text = item_data[ModClass.RUNE.value][0]

        # Rune mod text has this weird [text|text] format sometimes - the part after the pipe is all we need
        rune_mod_text = _process_mod_text(mod_text=rune_mod_text)

        new_rune = Rune(
            rune_name=rune_name,
            rune_effect=rune_mod_text
        )
        return [new_rune]

