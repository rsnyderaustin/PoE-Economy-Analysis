
import logging

from utils.enums import ModClass
from external_apis.trade_api import helper_funcs
from ..things import Rune


class RunesCreator:

    @classmethod
    def create_runes(cls, item_data: dict):
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

        # We can only deterministically get rune data when there is one rune mod text, because there isn't
        # any reliable way to pair runeMods text to each rune
        if len(item_data[ModClass.RUNE.value]) >= 2:
            return []

        rune_name = item_data['socketedItems'][0]['typeLine']
        rune_mod_text = item_data[ModClass.RUNE.value][0]
        rune_mod_values = helper_funcs.parse_values_from_mod_text(mod_text=rune_mod_text)

        socketed_item_dicts = item_data['socketedItems']
        num_socketed_items = len(socketed_item_dicts)
        value_per_mod = tuple(value / num_socketed_items for value in rune_mod_values if value)

        individual_rune_mod_text = helper_funcs.replace_mod_text_values(mod_text=rune_mod_text,
                                                                        replacement_values=value_per_mod)
        return [
            Rune(
                rune_name=rune_name,
                rune_effect=individual_rune_mod_text
            ) for _ in list(range(num_socketed_items))
        ]

