
import logging

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
        x=0





