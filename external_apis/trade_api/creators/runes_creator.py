
import logging
import re

from utils.enums import ModClass
from .. import helper_funcs
from ..things import Rune


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
        rune_mod_text = helper_funcs.remove_piped_brackets(text=rune_mod_text)

        new_rune = Rune(
            rune_name=rune_name,
            rune_effect=rune_mod_text
        )
        return [new_rune]

