
import logging
import rapidfuzz

from external_apis import CoECompiler, OfficialCompiler


class HybridMatchResult:

    def __init__(self, matched_mods, unmatched_mods):
        self.matched_mods = matched_mods
        self.unmatched_mods = unmatched_mods


def _swap_inc_dec_on_mod(mod_text: str):
    if "increased" in mod_text:
        return mod_text.replace("increased", "reduced")
    elif "reduced" in mod_text:
        return mod_text.replace("reduced", "increased")
    else:
        return mod_text


class CraftOfExileToOfficialPoe:

    def __init__(self, coe_compiler: craft_of_exile_api.CoECompiler, official_mod_data: dict):
        self.coe_compiler = coe_compiler
        self.official_mod_data = official_mod_data

        self.coe_mod_text_to_id = coe_compiler.mod_text_to_mod_id
        self.official_mod_text_to_id = self._format_official_mod_data_into_dict(official_mod_data)

    def _fuzzy_match_coe_mod_text(self, coe_mod_text) -> str | None:
        match, score, idx = rapidfuzz.process.extractOne(coe_mod_text, set(self.official_mod_text_to_id.keys()))
        logging.info(f"Craft of Exile mod '{coe_mod_text}' matched best with {match} at a fuzzy match score of {score}.")

        return match if match >= 85 else None

    @staticmethod
    def _format_official_mod_data_into_dict(official_mod_data) -> dict:
        official_mod_text_to_id = dict()
        for mod_class, mods_list in official_mod_data.items():
            for mod_data_dict in mods_list:
                official_id = mod_data_dict['id']
                mod_text = mod_data_dict['text'].lower()
                official_mod_text_to_id[mod_text] = official_id

        return official_mod_text_to_id

    def _match_hybrid_mod(self, coe_mod_text: str) -> HybridMatchResult:
        hybrid_mods = coe_mod_text.split(",")

        matched_mods = [mod for mod in hybrid_mods if mod in self.official_mod_text_to_id]
        unmatched_mods = [coe_mod for coe_mod in hybrid_mods if coe_mod not in self.official_mod_text_to_id]

        if len(hybrid_mods) == len(matched_mods):
            return HybridMatchResult(
                matched_mods=matched_mods,
                unmatched_mods=unmatched_mods
            )

        # Fuzzy match now
        fuzzy_matched_mods = [self._fuzzy_match_coe_mod_text(unmatched_mod) for unmatched_mod in unmatched_mods]
        matched_mods.extend(fuzzy_matched_mods)
        unmatched_mods = [mod for mod in unmatched_mods if mod not in fuzzy_matched_mods]

        return HybridMatchResult(
            matched_mods=matched_mods,
            unmatched_mods=unmatched_mods
        )

    def pair_non_matching_coe_mod_to_official(self, coe_mod_text: str, official_mod_texts: list[str]) -> str | None:
        match, score, idx = rapidfuzz.process.extractOne(coe_mod_text, official_mod_texts)

        return match if score >= 90 else None

    @classmethod
    def create_compiled_mods(cls, coe_compiler: CoECompiler, official_compiler: OfficialCompiler):
        coe_mod_text_to_id = coe_compiler.mod_text_to_mod_id

        # Attempt to pair CoE mod texts with Official PoE mod texts
        official_mod_id_to_coe_mod_id = dict()
        for coe_mod_text, coe_mod_id in coe_mod_text_to_id.items():
            coe_mod_text = coe_mod_text.replace('charm slots', 'charm slot')
            # If it's not in the official mod data then we suspect that it could be a hybrid mod or the increased/decreased is wonky
            if coe_mod_text not in self.official_mod_text_to_id:
                fuzzy_match = self._fuzzy_match_coe_mod_text(coe_mod_text=coe_mod_text)
                if fuzzy_match:
                    official_mod = official_api.OfficialMod(
                        mod_texts=[coe_mod_text],
                        mod_ids=[self.official_mod_text_to_id[coe_mod_text]]
                    )
                    coe_mod = craft_of_exile_api.CoEMod(
                        coe_mod_id=coe_mod_id,
                        mod_text=coe_mod_text
                    )

                hybrid_match_result = self._match_hybrid_mod(coe_mod_text=coe_mod_text)
                for matched_mod in hybrid_match_result.matched_mods:
                    official_mod_id = self.official_mod_text_to_id[matched_mod]
                    coe_mod_id = self.coe_mod_text_to_id[matched_mod]

                    official_mod_id_to_coe_mod_id[official_mod_id]
            else:
                poe_mod = official_api.OfficialMod(
                    mod_texts=[coe_mod_text],
                    mod_ids=[self.official_mod_text_to_id[coe_mod_text]]
                )


