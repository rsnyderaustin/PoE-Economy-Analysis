import logging
import rapidfuzz

from external_apis import CoECompiler, OfficialCompiler


class MatchResult:

    def __init__(self,
                 coe_mod_text: str,
                 official_mod_texts: list[str],
                 success: bool):
        self.coe_mod_text = coe_mod_text
        self.official_mod_texts = official_mod_texts
        self.success = success


def _swap_inc_dec_on_mod(mod_text: str):
    if "increased" in mod_text:
        return mod_text.replace("increased", "reduced")
    elif "reduced" in mod_text:
        return mod_text.replace("reduced", "increased")
    else:
        return mod_text


class ModsMatcher:

    def __init__(self, coe_mod_texts: set[str], official_mod_texts: set[str]):
        self.coe_mod_texts = coe_mod_texts
        self.official_mod_texts = official_mod_texts

    def match_mods(self) -> list[MatchResult]:
        matches = [self._match_coe_mod_text(coe_mod_text)
                   for coe_mod_text in self.coe_mod_texts]
        successful_matches = [match for match in matches
                              if match.success]
        unsuccessful_matches = [match for match in matches
                                if not match.success]

        logging.info(f"Successfully matched {len(successful_matches)} of {len(self.coe_mod_texts)} "
                     f"CoE mods.")
        if unsuccessful_matches:
            logging.info("Unsuccessfully matched CoE mods:\n%s",
                         "\n".join(f"\t{match.coe_mod_text}" for match in unsuccessful_matches))

        return successful_matches

    def _match_coe_mod_text(self, coe_mod_text: str) -> MatchResult:
        logging.info(f"Attempting to match CoE Mod '{coe_mod_text}'")
        if coe_mod_text in self.official_mod_texts:
            logging.info(f"\tMatched exactly to '{coe_mod_text}'")
            return MatchResult(
                coe_mod_text=coe_mod_text,
                official_mod_texts=[coe_mod_text],
                success=True
            )

        fuzzy_match = self._fuzzy_match_coe_mod_text(coe_mod_text)
        if fuzzy_match:
            logging.info(f"\tSuccessfully fuzzy matched to '{fuzzy_match}'")
            return MatchResult(
                coe_mod_text=coe_mod_text,
                official_mod_texts=[fuzzy_match],
                success=True
            )

        hybrid_matches = self._attempt_hybrid_match(coe_mod_text=coe_mod_text)
        if hybrid_matches:
            return MatchResult(
                coe_mod_text=coe_mod_text,
                official_mod_texts=hybrid_matches,
                success=True
            )

        return MatchResult(
            coe_mod_text=coe_mod_text,
            official_mod_texts=[],
            success=False
        )
    logging.info("\n")

    def _fuzzy_match_coe_mod_text(self, coe_mod_text) -> str | None:
        match, score, idx = rapidfuzz.process.extractOne(coe_mod_text, self.official_mod_texts)
        logging.info(
            f"Craft of Exile mod '{coe_mod_text}' matched best with '{match}' at a fuzzy match score of {score}.")

        if score >= 95:
            return match

        return None

    def _attempt_hybrid_match(self, coe_mod_text: str) -> list[str] | None:
        logging.info(f"\tAttempting to hybrid match.")
        hybrid_mods = coe_mod_text.split(",")

        matched_mods = [mod for mod in hybrid_mods if mod in self.official_mod_texts]
        unmatched_mods = [coe_mod for coe_mod in hybrid_mods if coe_mod not in self.official_mod_texts]

        if len(hybrid_mods) == len(matched_mods):
            return matched_mods

        logging.info(f"\t\tHybrid exactly matched to hybrids {matched_mods}.\nAttempting to fuzzy match {unmatched_mods}")

        # Fuzzy match the unmatched mods now
        fuzzy_matches = [self._fuzzy_match_coe_mod_text(unmatched_mod) for unmatched_mod in unmatched_mods]
        successful_fuzzies = [fuzzy_match for fuzzy_match in fuzzy_matches
                              if fuzzy_match is not None]
        logging.info(f"\t\tSuccessfully fuzzy matched hybrids {successful_fuzzies}")
        matched_mods.extend(successful_fuzzies)

        # We were only successful if all of the suspected hybrid mods were matched
        successfully_fuzzy_matched = len(hybrid_mods) == len(matched_mods)
        logging.info(f"\tFuzzy match success: {successfully_fuzzy_matched}")

        return matched_mods if successfully_fuzzy_matched else None
