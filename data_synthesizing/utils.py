

def parse_poecd_mtypes_string(mtypes_string: str) -> list:
    if not mtypes_string:
        return []
    parsed = [part for part in mtypes_string.split('|') if part]
    return parsed


class MatchScoreTracker:

    def __init__(self):
        self.sub_mod_to_poecd_mods = dict()
        self.poecd_mod_scores = dict()

    def score(self, sub_mod_id, poecd_mod_ids, score):
        for poecd_mod_id in poecd_mod_ids:
            if sub_mod_id not in self.sub_mod_to_poecd_mods:
                self.sub_mod_to_poecd_mods[sub_mod_id] = set()
            self.sub_mod_to_poecd_mods[sub_mod_id].add(poecd_mod_id)

            if poecd_mod_id not in self.poecd_mod_scores:
                self.poecd_mod_scores[poecd_mod_id] = set()
            self.poecd_mod_scores[poecd_mod_id].add(score)

    def determine_placements(self) -> list:
        if not self.sub_mod_to_poecd_mods:
            return []  # No data to process

        # Get mod IDs common to all sub mods
        matching_poecd_mod_ids = set.intersection(*self.sub_mod_to_poecd_mods.values())

        # Compute total scores
        score_totals = {
            poecd_mod_id: sum(scores)
            for poecd_mod_id, scores in self.poecd_mod_scores.items()
        }

        # Filter only those that are in the intersection set
        filtered_scores = {
            mod_id: total
            for mod_id, total in score_totals.items()
            if mod_id in matching_poecd_mod_ids
        }

        # Sort by score descending
        sorted_mods = sorted(filtered_scores.items(), key=lambda item: item[1], reverse=True)

        # Extract just the mod IDs in sorted order
        placement_order = [mod_id for mod_id, _ in sorted_mods]

        return placement_order



