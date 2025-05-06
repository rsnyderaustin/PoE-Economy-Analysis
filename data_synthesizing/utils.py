import re


def parse_poecd_mtypes_string(mtypes_string: str) -> list:
    if not mtypes_string:
        return []
    parsed = [part for part in mtypes_string.split('|') if part]
    return parsed


class MatchScoreTracker:

    def __init__(self):
        self.sub_mod_matches = dict()
        self.poecd_mod_scores = dict()

    def score_round(self, sub_mod_id, poecd_mod_ids, score):
        for poecd_mod_id in poecd_mod_ids:
            if sub_mod_id not in self.sub_mod_matches:
                self.sub_mod_matches[sub_mod_id] = set()
            self.sub_mod_matches[sub_mod_id].add(poecd_mod_id)

            if poecd_mod_id not in self.poecd_mod_scores:
                self.poecd_mod_scores[poecd_mod_id] = 0
            self.poecd_mod_scores[poecd_mod_id] += score

    def determine_winner(self) -> str | None:
        if not self.sub_mod_matches:
            return None  # No data to process

        winners = set.intersection(*self.sub_mod_matches.values())
        if len(winners) == 1:
            return next(iter(winners))

        best_poecd_mod = None
        highest_score = -1

        winner_scores = {
            mod_id: score_total
            for mod_id, score_total in self.poecd_mod_scores.items()
            if mod_id in winners
        }
        for winner_id, score_total in winner_scores.items():
            if score_total > highest_score:
                best_poecd_mod = winner_id
                highest_score = score_total

        return best_poecd_mod


def transform_text(text: str, transform_dict: dict) -> tuple:
    """
    :return: (Possibly transformed text , whether text was transformed)
    """
    transforms = {
        start: end
        for start, end in transform_dict.items()
        if start in text
    }

    for start, end in transforms.items():
        text = re.sub(re.escape(start), end, text)

    if transforms:
        transformed = True
    else:
        transformed = False

    return text, transformed





