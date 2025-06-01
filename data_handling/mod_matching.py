import copy
import re

import rapidfuzz

from instances_and_definitions import ItemMod
from poe2db_scrape.mods_management import Poe2DbModsManager, create_mod_id, Poe2DbMod


class _MatchScoreTracker:

    def __init__(self):
        self._sub_mod_matches = dict()
        self._poe2db_mod_scores = dict()

    def score_round(self, sub_mod_id, poe2db_mods: set[Poe2DbMod], score):
        for poe2db_mod in poe2db_mods:
            if sub_mod_id not in self._sub_mod_matches:
                self._sub_mod_matches[sub_mod_id] = set()

            self._sub_mod_matches[sub_mod_id].add(poe2db_mod)

            if poe2db_mod not in self._poe2db_mod_scores:
                self._poe2db_mod_scores[poe2db_mod] = 0
            self._poe2db_mod_scores[poe2db_mod] += score

    def determine_winner(self) -> Poe2DbMod | None:
        if not self._sub_mod_matches:
            return None  # No data to process

        winners = set.intersection(*self._sub_mod_matches.values())
        if len(winners) == 1:
            return next(iter(winners))

        best_poe2db_mod = None
        highest_score = -1

        winner_scores = {
            mod: score_total
            for mod, score_total in self._poe2db_mod_scores.items()
            if mod in winners
        }
        for winner, score_total in winner_scores.items():
            if score_total > highest_score:
                best_poe2db_mod = winner
                highest_score = score_total

        return best_poe2db_mod


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

    def __init__(self, poe2db_mods_manager: Poe2DbModsManager):
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

        self._poe2db_mods_manager = poe2db_mods_manager

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

    def _attempt_hybrid_match(self, item_mod: ItemMod, min_score: float) -> Poe2DbMod | None:
        atype_manager = self._poe2db_mods_manager.fetch_atype_manager(atype=item_mod.atype)
        hybrid_scores_tracker = _MatchScoreTracker()

        number_of_parts = len(item_mod.sub_mods)

        """
        So this whole block works by matching individual PoE Trade hybrid mod (SubMod) texts to the possible
        hybrid poe2db mod texts of the corresponding AType. After we've found the best matches
        for each hybrid mod text, we just determine which poe2db hybrid mod is the best fit
        """
        for sub_mod in item_mod.sub_mods:
            mod_part_to_parent_dict = atype_manager.fetch_hybrid_part_to_parents(item_mod.affix_type)
            hybrid_mod_texts = list(mod_part_to_parent_dict.keys())

            matches = rapidfuzz.process.extract(sub_mod.sanitized_text,
                                                hybrid_mod_texts,
                                                score_cutoff=min_score)

            for match, score, idx in matches:
                poe2db_mods = mod_part_to_parent_dict[match]

                # The number of parts in the Mod text has to line up with the number of parts in the poe2db mod
                valid_poe2db_mods = {
                    poe2db_mod
                    for poe2db_mod in poe2db_mods
                    if atype_manager.determine_number_of_hybrid_parts(poe2db_mod) == number_of_parts
                }

                if not valid_poe2db_mods:
                    continue

                hybrid_scores_tracker.score_round(sub_mod_id=sub_mod.sub_mod_hash,
                                                  poe2db_mods=valid_poe2db_mods,
                                                  score=score)

        poe2db_mod_match = hybrid_scores_tracker.determine_winner()
        return poe2db_mod_match

    def _attempt_singleton_match(self, item_mod: ItemMod, min_score: float) -> Poe2DbMod:
        atype_manager = self._poe2db_mods_manager.fetch_atype_manager(atype=item_mod.atype)

        poe2db_mod_texts = atype_manager.fetch_mod_texts(item_mod.affix_type)

        mod_text = item_mod.sub_mods[0].sanitized_text

        result = rapidfuzz.process.extractOne(mod_text,
                                              poe2db_mod_texts,
                                              score_cutoff=min_score)
        if not result:
            return None

        match, score, idx = result

        mod_id = create_mod_id(atype=atype_manager.atype,
                               mod_text=match,
                               affix_type=item_mod.affix_type)
        mod = atype_manager.fetch_mod(mod_id)

        return mod

    def _attempt_match(self, item_mod: ItemMod, min_score: float, attempt_to_transform: bool = False) -> Poe2DbMod | None:
        if attempt_to_transform:
            item_mod = copy.deepcopy(item_mod)
            for sub_mod in item_mod.sub_mods:
                sub_mod.sanitized_text = self._transform_text(sub_mod.sanitized_text)

        if item_mod.is_hybrid:
            mod_match = self._attempt_hybrid_match(item_mod, min_score)
        else:
            mod_match = self._attempt_singleton_match(item_mod, min_score)

        return mod_match

    def match_mod(self, item_mod: ItemMod) -> Poe2DbMod | None:
        """

        :param item_mod:
        :return: The matching poe2db Mod ID.
        """

        poe2db_mod_match = self._attempt_match(item_mod=item_mod, min_score=95.0)
        if poe2db_mod_match:
            return poe2db_mod_match

        poe2db_mod_match = self._attempt_match(item_mod=item_mod, min_score=95.0, attempt_to_transform=True)
        if poe2db_mod_match:
            return poe2db_mod_match

        poe2db_mod_match = self._attempt_match(item_mod=item_mod, min_score=90.0)
        if poe2db_mod_match:
            return poe2db_mod_match

        poe2db_mod_match = self._attempt_match(item_mod=item_mod, min_score=90.0, attempt_to_transform=True)
        if poe2db_mod_match:
            return poe2db_mod_match
