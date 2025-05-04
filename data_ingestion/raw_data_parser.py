import logging

from instances_and_definitions import ItemSocketer, ModClass
from shared.utils import remove_piped_brackets


class RawDataParser:

    @classmethod
    def create_socketer_for_internal_storage(cls, item_data: dict) -> ItemSocketer | None:
        """
        We can only determine socketer effects from items with only one socketer.
        """
        if ModClass.RUNE.value not in item_data:
            logging.info(f"Requested to create runes when item does not have {ModClass.RUNE.value} attribute."
                         f"\nItem data:\n{item_data}.")
            return None

        # We can only deterministically get rune data when there is one rune socketed, because different types of the same
        # data_ingesting can produce one rune text
        if len(item_data['socketedItems']) >= 2:
            logging.info(f"Item has more than one socketer. Skipping.")
            return None

        logging.info("Item only has one socketer. Creating rune.")

        rune_name = item_data['socketedItems'][0]['typeLine']
        rune_mod_text = item_data[ModClass.RUNE.value][0]

        # Rune mod text has this weird [text|text] format sometimes - the part after the pipe is all we need
        rune_mod_text = remove_piped_brackets(text=rune_mod_text)

        item_socketer = ItemSocketer(
            name=rune_name,
            text=rune_mod_text
        )
        return item_socketer


    @classmethod
    def create_item_mods(cls, item_data: dict):
