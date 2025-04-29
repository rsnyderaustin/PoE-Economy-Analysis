from .mods_matcher import MatchResult
from external_apis import OfficialModsManager, CoEModsManager
from compiled_data.mods_management.compiled_mod import CompiledMod


class CompiledModFactory:

    @classmethod
    def create_compiled_mods(cls,
                             coe_mods_manager: CoEModsManager,
                             official_mods_manager: OfficialModsManager,
                             match_results: list[MatchResult]) -> set[CompiledMod]:
        compiled_mods = set()
        for match_result in match_results:
            coe_mod = coe_mods_manager.fetch_mod(mod_text=match_result.coe_mod_text)
            official_mods = [
                official_mods_manager.fetch_mod(mod_text=official_mod_text)
                for official_mod_text in match_result.official_mod_texts
            ]

            new_compiled_mod = CompiledMod(
                coe_mod_id=coe_mod.mod_id,
                official_mod_ids=[official_mod.mod_id for official_mod in official_mods],
                readable_mod_text=coe_mod.mod_text,
                mod_types=coe_mod.mod_types,
                affix_type=coe_mod.affix_type
            )
            compiled_mods.add(new_compiled_mod)

        return compiled_mods
