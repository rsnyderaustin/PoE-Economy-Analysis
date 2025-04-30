
from compiled_data import ApisCompiler


class ProgramManager:

    def __init__(self):
        api_compiler = ApisCompiler()
        global_mods_manager = api_compiler.compile_into_global_btypes_manager()
        x=0