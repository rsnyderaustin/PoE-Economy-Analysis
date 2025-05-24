import logging
import re

from instances_and_definitions import ItemMod
from poecd_api.data_management import PoecdMod
from shared import shared_utils


class MatchScoreTracker:

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





