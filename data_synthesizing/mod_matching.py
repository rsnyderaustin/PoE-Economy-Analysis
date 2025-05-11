import logging

import rapidfuzz

import file_management
from file_management import FileKey
from instances_and_definitions import ItemMod, ModClass
from poecd_api.data_management import GlobalAtypesManager
from shared import shared_utils
from . import utils


class ModMatcher:

    def __init__(self, global_atypes_manager: GlobalAtypesManager):
        self.mod_transformations = {
            '# additional': 'an additional',
            'an additional': '# additional',
            'reduced': 'increased',
            'increased': 'reduced'
        }

        self._coe_mod_parts_to_remove = {
            '#% increased Waystones found in Area',
            '#% reduced Waystones found in Area'
        }

        self._global_atypes_manager = global_atypes_manager

    def _attempt_hybrid_match(self,
                              item_mod: ItemMod,
                              atype_manager,
                              min_score: float,
                              attempt_to_transform: bool = False) -> str | None:

        hybrid_scores_tracker = utils.MatchScoreTracker()

        number_of_parts = len(item_mod.sub_mods)

        # So this whole block works by matching individual PoE Trade hybrid mod (SubMod) texts to the possible
        # hybrid mod texts of the corresponding AType (data sourced from Poecd). After we've found the best matches
        # for each hybrid mod text, we just determine which Poecd hybrid mod is the most fititng
        for sub_mod in item_mod.sub_mods:
            mod_to_parent_dict = (atype_manager.hybrid_parts_to_parent_affixed_dict[item_mod.affix_type]
                                  if item_mod.affix_type else atype_manager.hybrid_parts_to_parent_dict)
            hybrid_mod_texts = list(mod_to_parent_dict.keys())

            if attempt_to_transform:
                sub_mod_text = utils.transform_text(sub_mod.sanitized_mod_text,
                                                    transform_dict=self.mod_transformations)[0]
            else:
                sub_mod_text = sub_mod.sanitized_mod_text
            matches = rapidfuzz.process.extract(sub_mod_text,
                                                hybrid_mod_texts,
                                                score_cutoff=min_score)

            for match, score, idx in matches:
                poecd_mod_ids = mod_to_parent_dict[match]

                # The number of parts in the Mod text has to line up with the number of parts in the Poecd mod
                poecd_mod_ids = {
                    mod_id
                    for mod_id in poecd_mod_ids
                    if atype_manager.num_hybrid_parts_dict[mod_id] == number_of_parts
                }

                if not poecd_mod_ids:
                    continue

                hybrid_scores_tracker.score_round(sub_mod_id=sub_mod.mod_id,
                                                  poecd_mod_ids=poecd_mod_ids,
                                                  score=score)

        poecd_mod_id_match = hybrid_scores_tracker.determine_winner()
        return poecd_mod_id_match

        if not item_mod.is_hybrid:
            if item_mod.affix_type:
                poecd_mod_texts = list(atype_manager.mods_affixed_dict[item_mod.affix_type].keys())
            else:
                poecd_mod_texts = list(atype_manager.mods_dict.keys())

            if attempt_to_transform:
                mod_text = utils.transform_text(item_mod.sub_mods[0].sanitized_mod_text,
                                                transform_dict=self.mod_transformations)[0]
            else:
                mod_text = item_mod.sub_mods[0].sanitized_mod_text

            result = rapidfuzz.process.extractOne(mod_text,
                                                  poecd_mod_texts,
                                                  score_cutoff=min_score)
            if result:
                match, score, idx = result

                mod = atype_manager.mods_affixed_dict[item_mod.affix_type][match]
                return mod.mod_id
            else:
                return None

    def _match_mod(self, item_mod: ItemMod) -> str | None:
        """

        :param item_mod:
        :return: The matching Poecd Mod ID.
        """

        atype_manager = self._global_atypes_manager.fetch_atype_manager(atype_name=item_mod.atype)

        coe_mod_id_match = self._attempt_match(item_mod=item_mod,
                                               atype_manager=atype_manager,
                                               min_score=95.0)
        if coe_mod_id_match:
            return coe_mod_id_match

        coe_mod_id_match = self._attempt_match(item_mod=item_mod,
                                               atype_manager=atype_manager,
                                               min_score=95.0,
                                               attempt_to_transform=True)
        if coe_mod_id_match:
            return coe_mod_id_match

        coe_mod_id_match = self._attempt_match(item_mod=item_mod,
                                               atype_manager=atype_manager,
                                               min_score=90.0)
        if coe_mod_id_match:
            return coe_mod_id_match

        coe_mod_id_match = self._attempt_match(item_mod=item_mod,
                                               atype_manager=atype_manager,
                                               min_score=90.0,
                                               attempt_to_transform=True)
        if coe_mod_id_match:
            return coe_mod_id_match



