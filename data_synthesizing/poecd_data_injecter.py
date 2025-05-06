import logging

import rapidfuzz

from instances_and_definitions import ItemMod, ModClass
from . import utils
from external_apis.poecd_data import PoecdDataManager


class PoecdDataInjecter:

    def __init__(self):

        self._coe_mod_match_replacements = {
            '# additional': 'an additional',
            'an additional': '# additional',
            'reduced': 'increased',
            'increased': 'reduced'
        }

        self._coe_mod_parts_to_remove = {
            '#% increased Waystones found in Area',
            '#% reduced Waystones found in Area'
        }

        self._poecd_manager = PoecdDataManager()

    def inject_poecd_data_into_mod(self, item_mod: ItemMod):
        atype_manager = self._poecd_manager.atype_data_managers[item_mod.atype]
        poecd_mod_id = self._match_mod(item_mod)

        # Implicit mods don't have weights, and we don't have weights for corruption enchantments yet
        if item_mod.mod_class not in [ModClass.IMPLICIT, ModClass.ENCHANT]:
            weighting = atype_manager.fetch_mod_weighting(mod_id=poecd_mod_id,
                                                          atype=item_mod.atype,
                                                          ilvl=item_mod.mod_ilvl)
            item_mod.weighting = weighting

        mod_types = atype_manager.fetch_mod_types(mod_id=poecd_mod_id)
        item_mod.mod_types = mod_types

    def _match_mod(self, item_mod: ItemMod) -> str:
        """

        :param item_mod:
        :return: The matching Poecd Mod ID.
        """

        atype_manager = self._poecd_manager.atype_data_managers[item_mod.atype]
        mods = atype_manager.mods

        if item_mod.is_hybrid:
            logging.info(f"\nHybrid mod match:{[sub_mod.mod_text for sub_mod in item_mod.sub_mods]}\n")
            hybrid_scores_tracker = utils.MatchScoreTracker()

            # So this whole block works by matching individual PoE Trade hybrid mod (SubMod) texts to the possible
            # hybrid mod texts of the corresponding AType (data sourced from Poecd). After we've found the best matches
            # for each hybrid mod text, we just determine which Poecd hybrid mod is the most fititng
            for sub_mod in item_mod.sub_mods:

                matches = rapidfuzz.process.extract(sub_mod.mod_text,
                                                    atype_manager.fetch_hybrid_mod_texts(atype=item_mod.atype),
                                                    score_cutoff=95.0)

                for match, score, idx in matches:
                    poecd_mod_ids = atype_manager.fetch_hybrid_mod_ids(atype=item_mod.atype)

                    hybrid_scores_tracker.score(sub_mod_id=sub_mod.mod_id,
                                                poecd_mod_ids=poecd_mod_ids,
                                                score=score)
                logging.info("\n")

            mod_id_score_order = hybrid_scores_tracker.determine_placements()
            for mod_id in mod_id_score_order:
                if atype_manager.mod_id_to_affix_type[mod_id] == item_mod.affix_type:
                    return mod_id

        if not item_mod.is_hybrid:
            matches = rapidfuzz.process.extract(item_mod.sub_mods[0].mod_text,
                                                atype_manager.mod_text_to_id.keys(),
                                                score_cutoff=95)
            for match, score, idx in matches:
                poecd_mod_id = atype_manager.fetch_mod_id(atype=item_mod.atype,
                                                          mod_text=match,
                                                          affix_type=item_mod.affix_type)
                # fetch_mod_id returns None if there is no Mod ID found
                if poecd_mod_id:
                    logging.info(f"\nSingleton mod match: "
                                 f"\n\tTrade mod: {item_mod.sub_mods[0].mod_text}:"
                                 f"\n\tPoecd mod: {match}"
                                 f"\n\tScore: {score}")
                    return poecd_mod_id
