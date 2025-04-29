from .mods_matcher import ModsMatcher
from .compiled_mod_factory import CompiledModFactory
from compiled_data.mods_management.base_item_type_mods_manager import BaseItemTypeModsManager
from external_apis import (CoECompiler, CoEDataPuller, CoEEndpoint, OfficialCompiler,
                           OfficialDataPuller, CoEJsonPath)


class ApisCompiler:

    def __init__(self):
        pass

    def _create_mods(self):
        pass

    @classmethod
    def compile(cls):
        coe_mods_data = CoEDataPuller.pull_data(json_file_path=CoEJsonPath.PATH.value)
        coe_bases_data = CoEDataPuller.pull_data(endpoint=CoEEndpoint.BASE_TYPES)
        coe_compiler = CoECompiler(
            mods_data=coe_mods_data,
            bases_data=coe_bases_data
        )

        official_stats_data = OfficialDataPuller.pull_stats_data()
        official_static_data = OfficialDataPuller.pull_static_data()
        official_compiler = OfficialCompiler(
            stats_data=official_stats_data,
            static_data=official_static_data
        )

        mods_matcher = ModsMatcher(
            coe_mod_texts=coe_compiler.mods_manager.mod_texts,
            official_mod_texts=official_compiler.mods_manager.mod_texts
        )
        mod_matches = mods_matcher.match_mods()
        compiled_mods = CompiledModFactory.create_compiled_mods(
            coe_mods_manager=coe_compiler.mods_manager,
            official_mods_manager=official_compiler.mods_manager,
            match_results=mod_matches
        )
        base_type_to_mods_manager = dict()
        compiled_mods_manager = BaseItemTypeModsManager()
        for compiled_mod in compiled_mods:
            base_type = compiled_mod.base
            compiled_mods_manager.add_compiled_mod(compiled_mod)

        for mod_tier in coe_compiler.mod_tiers_generator():
            # Mods that were not matched between CoE and the Official API were not compiled into a mod,
            # so we skip those
            if mod_tier.coe_mod_id not in compiled_mods_manager.coe_mod_ids:
                continue
            compiled_mod = compiled_mods_manager.fetch_compiled_mod(coe_mod_id=mod_tier.coe_mod_id)
            base_item_type_manager = base_item_type_managers[mod_tier.base_type_id]
            base_item_type_manager.add_mod_tier(
                base_type_id=mod_tier.base_type_id,
                coe_mod_id=mod_tier.base_type_id,
                mod=compiled_mod,
                ilvl=mod_tier.ilvl,
                values_range=mod_tier.values_range,
                weighting=mod_tier.weighting
            )
        return base_item_type_managers









