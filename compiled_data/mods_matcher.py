import logging
import rapidfuzz

from external_apis import CoECompiler, OfficialCompiler


class MatchResult:

    def __init__(self,
                 coe_mod_text: str,
                 official_mod_texts: list[str],
                 match_score: float,
                 success: bool,
                 unsuccessful_official_hybrid_matches: list[str] = None):
        """

        :param coe_mod_text:
        :param official_mod_texts: Official mod texts that were successfully matched with CoE mod text.
        :param match_score:
        :param success:
        :param unsuccessful_official_hybrid_matches:
        """
        self.coe_mod_text = coe_mod_text
        self.official_mod_texts = official_mod_texts
        self.match_score = match_score
        self.success = success

        self.unsuccessful_official_hybrid_matches = unsuccessful_official_hybrid_matches or []


class ModsMatcher:

    def __init__(self, coe_mod_texts: set[str], official_mod_texts: set[str]):
        self.coe_mod_texts = coe_mod_texts
        self.official_mod_texts = official_mod_texts

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

    def match_mods(self) -> list[MatchResult]:
        match_results = []
        for coe_mod_text in self.coe_mod_texts:
            match_result = self._match_coe_mod_text(coe_mod_text)
            if not match_result.success:
                match_result = self._match_coe_mod_text(coe_mod_text,
                                                        replace_and_remove=True)

            match_results.append(match_result)

        successful_matches = [match for match in match_results
                              if match.success]
        unsuccessful_matches = [match for match in match_results
                                if not match.success]

        logging.info(f"Successfully matched {len(successful_matches)} of {len(self.coe_mod_texts)} "
                     f"CoE mods.")
        if unsuccessful_matches:
            logging.info("Unsuccessfully matched CoE mods:\n%s",
                         "\n".join(f"\t{match.coe_mod_text}" for match in unsuccessful_matches))

        return successful_matches

    def _match_coe_mod_text(self, coe_mod_text: str, replace_and_remove: bool = False) -> MatchResult:
        logging.info(f"\nAttempting to match CoE Mod '{coe_mod_text}'")
        if coe_mod_text in self.official_mod_texts:
            logging.info(f"\tMatched exactly to '{coe_mod_text}'")
            return MatchResult(
                coe_mod_text=coe_mod_text,
                official_mod_texts=[coe_mod_text],
                match_score=100.0,
                success=True
            )

        fuzzy_match = self._fuzzy_match_coe_mod_text(coe_mod_text,
                                                     min_fuzzy_score=95,
                                                     replace_and_remove=replace_and_remove)
        if fuzzy_match.success:
            logging.info(f"\tSuccessfully fuzzy matched to '{fuzzy_match}' with a score of {fuzzy_match.match_score}")
            return fuzzy_match

        hybrid_match = self._attempt_hybrid_match(coe_mod_text=coe_mod_text,
                                                  min_fuzzy_score=95,
                                                  replace_and_remove=replace_and_remove)
        if hybrid_match.success:
            return hybrid_match

        fuzzy_match = self._fuzzy_match_coe_mod_text(coe_mod_text,
                                                     min_fuzzy_score=90,
                                                     replace_and_remove=replace_and_remove)
        if fuzzy_match.success:
            logging.info(f"\tSuccessfully fuzzy matched to '{fuzzy_match}'")
            return fuzzy_match

        hybrid_match = self._attempt_hybrid_match(coe_mod_text=coe_mod_text,
                                                  min_fuzzy_score=90,
                                                  replace_and_remove=replace_and_remove)

        return hybrid_match

    def _fuzzy_match_coe_mod_text(self,
                                  coe_mod_text: str,
                                  min_fuzzy_score: int,
                                  replace_and_remove: bool = False) -> MatchResult:
        match, orig_score, idx = rapidfuzz.process.extractOne(coe_mod_text, self.official_mod_texts)
        logging.info(
            f"Craft of Exile mod '{coe_mod_text}'\nmatched best with '{match}' at a fuzzy match score of {orig_score}.")

        was_success = (orig_score >= min_fuzzy_score)

        if was_success:
            return MatchResult(
                coe_mod_text=coe_mod_text,
                official_mod_texts=[match],
                success=was_success,
                match_score=orig_score
            )

        if replace_and_remove:
            for original_str, replacement_str in self._coe_mod_match_replacements.items():
                if original_str in coe_mod_text:
                    replaced_mod_text = coe_mod_text.replace(original_str, replacement_str)
                    match, score, idx = rapidfuzz.process.extractOne(replaced_mod_text, self.official_mod_texts)

                    if score >= min_fuzzy_score:
                        return MatchResult(
                            coe_mod_text=coe_mod_text,
                            official_mod_texts=[match],
                            success=True,
                            match_score=score
                        )

            for remove_str in self._coe_mod_parts_to_remove:
                if remove_str in coe_mod_text:
                    return MatchResult(
                        coe_mod_text=coe_mod_text,
                        official_mod_texts=[],
                        success=True,
                        match_score=100
                    )

        return MatchResult(
            coe_mod_text=coe_mod_text,
            official_mod_texts=[match],
            success=was_success,
            match_score=orig_score
        )


    def _attempt_hybrid_match(self, coe_mod_text: str, min_fuzzy_score: int, replace_and_remove: bool = False) -> MatchResult:
        logging.info(f"\tAttempting to hybrid match {coe_mod_text} with a minimum fuzzy score of {min_fuzzy_score}.")
        hybrid_mods = coe_mod_text.split(",")
        hybrid_mods = [hybrid_mod.strip() for hybrid_mod in hybrid_mods]

        matched_mods = [mod for mod in hybrid_mods if mod in self.official_mod_texts]
        unmatched_mods = [coe_mod for coe_mod in hybrid_mods if coe_mod not in self.official_mod_texts]

        if len(hybrid_mods) == len(matched_mods):
            return MatchResult(
                coe_mod_text=coe_mod_text,
                official_mod_texts=matched_mods,
                match_score=100,
                success=True
            )

        # Fuzzy match the unmatched hybrid mods now
        fuzzy_matches = [self._fuzzy_match_coe_mod_text(unmatched_mod,
                                                        min_fuzzy_score=min_fuzzy_score,
                                                        replace_and_remove=replace_and_remove)
                         for unmatched_mod in unmatched_mods]
        successful_fuzzies = [fuzzy_match for fuzzy_match in fuzzy_matches
                              if fuzzy_match.success]
        unsuccessful_fuzzies = [fuzzy_match for fuzzy_match in fuzzy_matches
                                if not fuzzy_match.success]

        successful_official_mod_text_matches = [
            *[official_mod_text
              for fuzzy_match_result in successful_fuzzies
              for official_mod_text in fuzzy_match_result.official_mod_texts],
            *matched_mods
        ]
        min_match_score = min([fuzzy_match.match_score for fuzzy_match in fuzzy_matches])

        # Successful fuzzy hybrid
        if all([fuzzy_match_result.success for fuzzy_match_result in fuzzy_matches]):
            return MatchResult(
                coe_mod_text=coe_mod_text,
                official_mod_texts=successful_official_mod_text_matches,
                success=True,
                match_score=min_match_score
            )
        # Unsuccessful fuzzy hybrid
        else:
            return MatchResult(
                coe_mod_text=coe_mod_text,
                official_mod_texts=successful_official_mod_text_matches,
                match_score=min_match_score,
                success=False,
                unsuccessful_official_hybrid_matches=[
                    official_mod_text
                    for fuzzy_match_result in unsuccessful_fuzzies
                    for official_mod_text in fuzzy_match_result.official_mod_texts]
            )
