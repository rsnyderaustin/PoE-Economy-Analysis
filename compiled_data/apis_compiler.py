from .mods_matcher import ModsMatcher
from .mods_management import CompiledModsManager
from .compiled_mod_factory import CompiledModFactory
from compiled_data.mods_management.btype_mods_manager import BtypeModsManager
from external_apis import (CoECompiler, CoEDataPuller, CoEEndpoint, OfficialCompiler,
                           OfficialDataPuller, CoEJsonPath)
from .global_btypes_manager import GlobalBtypesManager


class ApisCompiler:

    def __init__(self):
        coe_mods_data = CoEDataPuller.pull_data(json_file_path=CoEJsonPath.PATH.value)
        coe_bases_data = CoEDataPuller.pull_data(endpoint=CoEEndpoint.BASE_TYPES)
        self.coe_compiler = CoECompiler(
            mods_data=coe_mods_data,
            bases_data=coe_bases_data
        )

        official_stats_data = OfficialDataPuller.pull_stats_data()
        official_static_data = OfficialDataPuller.pull_static_data()
        self.official_compiler = OfficialCompiler(
            stats_data=official_stats_data,
            static_data=official_static_data
        )
        x=0

    def _create_mods(self):
        pass

    def _insert_compiled_mods_into_global_manager(self,
                                                  global_mods_manager: GlobalBtypesManager,
                                                  compiled_mods_manager: CompiledModsManager):
        for btype_name, coe_mod_ids in self.coe_compiler.btype_name_to_mod_ids.items():
            compiled_mods = [
                compiled_mods_manager.fetch_compiled_mod(coe_mod_id=coe_mod_id)
                for coe_mod_id in coe_mod_ids
                if coe_mod_id in compiled_mods_manager.coe_mod_ids
            ]
            btye_manager = global_mods_manager.fetch_btype_mod_manager(btype_name=btype_name)
            for compiled_mod in compiled_mods:
                btye_manager.add_compiled_mod(compiled_mod=compiled_mod)

    def _insert_mod_tiers_into_global_manager(self,
                                              valid_coe_mod_ids: set[int],
                                              global_mods_manager: GlobalBtypesManager):
        for coe_mod_tier in self.coe_compiler.mod_tiers_generator():
            # Mods that were not matched between CoE and the Official API were not compiled into a mod,
            # so we skip those
            if coe_mod_tier.coe_mod_id not in valid_coe_mod_ids:
                continue

            btype_manager = global_mods_manager.fetch_btype_mod_manager(btype_name=coe_mod_tier.btype_name)
            btype_manager.add_mod_tier(coe_mod_tier)

    def compile_into_global_btypes_manager(self) -> GlobalBtypesManager:

        mods_matcher = ModsMatcher(
            coe_mod_texts=self.coe_compiler.mods_manager.mod_texts,
            official_mod_texts=self.official_compiler.mods_manager.mod_texts
        )
        mod_matches = mods_matcher.match_mods()

        missing_mod_texts = [
            match.coe_mod_text
            for match in mod_matches
            if match.coe_mod_text not in self.coe_compiler.valid_coe_mod_texts
        ]
        compiled_mods = CompiledModFactory.create_compiled_mods(
            coe_mods_manager=self.coe_compiler.mods_manager,
            official_mods_manager=self.official_compiler.mods_manager,
            match_results=mod_matches
        )

        compiled_mods_manager = CompiledModsManager()
        for compiled_mod in compiled_mods:
            compiled_mods_manager.add_compiled_mod(compiled_mod)

        global_mods_manager = GlobalBtypesManager(
            btype_mods_managers=[
                BtypeModsManager(btype_name)
                for btype_name in self.coe_compiler.valid_btype_names
            ]
        )

        missing_mod_ids = [
            mod_id for mod_id in self.coe_compiler.valid_coe_mod_ids
            if mod_id not in compiled_mods_manager.coe_mod_ids
        ]

        self._insert_compiled_mods_into_global_manager(
            global_mods_manager=global_mods_manager,
            compiled_mods_manager=compiled_mods_manager
        )


        self._insert_mod_tiers_into_global_manager(
            valid_coe_mod_ids=set(
                self.coe_compiler.mod_text_to_mod_id[mod_match.coe_mod_text] for mod_match in mod_matches
            ),
            global_mods_manager=global_mods_manager
        )
        return global_mods_manager









