import copy
import re

import rapidfuzz

from instances_and_definitions import ItemMod
from poecd_api.mods_management import GlobalAtypesManager
from data_handling.mods import utils


class _MatchScoreTracker:

    def __init__(self):
        self._sub_mod_matches = dict()
        self._poecd_mod_scores = dict()

    def score_round(self, sub_mod_id, poecd_mod_ids, score):
        for poecd_mod_id in poecd_mod_ids:
            if sub_mod_id not in self._sub_mod_matches:
                self._sub_mod_matches[sub_mod_id] = set()
            self._sub_mod_matches[sub_mod_id].add(poecd_mod_id)

            if poecd_mod_id not in self._poecd_mod_scores:
                self._poecd_mod_scores[poecd_mod_id] = 0
            self._poecd_mod_scores[poecd_mod_id] += score

    def determine_winner(self) -> str | None:
        if not self._sub_mod_matches:
            return None  # No data to process

        winners = set.intersection(*self._sub_mod_matches.values())
        if len(winners) == 1:
            return next(iter(winners))

        best_poecd_mod = None
        highest_score = -1

        winner_scores = {
            mod_id: score_total
            for mod_id, score_total in self._poecd_mod_scores.items()
            if mod_id in winners
        }
        for winner_id, score_total in winner_scores.items():
            if score_total > highest_score:
                best_poecd_mod = winner_id
                highest_score = score_total

        return best_poecd_mod


def transform_text(text: str, transform_dict: dict) -> str:
    """
    :return: Possibly transformed text
    """
    transforms = {
        before: after
        for before, after in transform_dict.items()
        if before in text
    }

    for before, after in transforms.items():
        text = re.sub(re.escape(before), after, text)

    return text


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

    def _transform_text(self, text: str) -> str:
        """
        :return: Possibly transformed text
        """
        transforms = {
            before: after
            for before, after in self.mod_transformations.items()
            if before in text
        }

        for before, after in transforms.items():
            text = re.sub(re.escape(before), after, text)

        return text

    def _attempt_hybrid_match(self, item_mod: ItemMod, min_score: float) -> str | None:
        atype_manager = self._global_atypes_manager.fetch_atype_manager(atype_name=item_mod.atype)
        hybrid_scores_tracker = utils.MatchScoreTracker()

        number_of_parts = len(item_mod.sub_mods)

        """
        So this whole block works by matching individual PoE Trade hybrid mod (SubMod) texts to the possible
        hybrid Poecd mod texts of the corresponding AType. After we've found the best matches
        for each hybrid mod text, we just determine which Poecd hybrid mod is the best fit
        """
        for sub_mod in item_mod.sub_mods:
            mod_to_parent_dict = (atype_manager.hybrid_parts_to_parent_affixed_dict[item_mod.affix_type_e]
                                  if item_mod.affix_type_e else atype_manager.hybrid_parts_to_parent_dict)
            hybrid_mod_texts = list(mod_to_parent_dict.keys())

            matches = rapidfuzz.process.extract(sub_mod.sanitized_mod_text,
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

    def _attempt_singleton_match(self, item_mod: ItemMod, min_score: float):
        atype_manager = self._global_atypes_manager.fetch_atype_manager(atype_name=item_mod.atype)
        if item_mod.affix_type_e:
            poecd_mod_texts = list(atype_manager._mods_affixed_dict[item_mod.affix_type_e].keys())
        else:
            poecd_mod_texts = list(atype_manager.mods_dict.keys())

        mod_text = item_mod.sub_mods[0].sanitized_mod_text

        result = rapidfuzz.process.extractOne(mod_text,
                                              poecd_mod_texts,
                                              score_cutoff=min_score)
        if not result:
            return None

        match, score, idx = result

        mod = atype_manager.fetch_mod(mod_text=match,
                                      affix_type=item_mod.affix_type_e)

        return mod.mod_id

    def _attempt_match(self, item_mod: ItemMod, min_score: float, attempt_to_transform: bool = False) -> str | None:
        if attempt_to_transform:
            item_mod = copy.deepcopy(item_mod)
            for sub_mod in item_mod.sub_mods:
                sub_mod.sanitized_mod_text = utils.transform_text(sub_mod.sanitized_mod_text,
                                                                  transform_dict=self.mod_transformations)
        if item_mod.is_hybrid:
            match = self._attempt_hybrid_match(item_mod, min_score)
        else:
            match = self._attempt_singleton_match(item_mod, min_score)

        return match

    def match_mod(self, item_mod: ItemMod) -> str | None:
        """

        :param item_mod:
        :return: The matching Poecd Mod ID.
        """

        coe_mod_id_match = self._attempt_match(item_mod=item_mod, min_score=95.0)
        if coe_mod_id_match:
            return coe_mod_id_match

        coe_mod_id_match = self._attempt_match(item_mod=item_mod, min_score=95.0, attempt_to_transform=True)
        if coe_mod_id_match:
            return coe_mod_id_match

        coe_mod_id_match = self._attempt_match(item_mod=item_mod, min_score=90.0)
        if coe_mod_id_match:
            return coe_mod_id_match

        coe_mod_id_match = self._attempt_match(item_mod=item_mod, min_score=90.0, attempt_to_transform=True)
        if coe_mod_id_match:
            return coe_mod_id_match
