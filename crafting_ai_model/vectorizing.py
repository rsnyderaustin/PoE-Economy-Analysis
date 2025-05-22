from instances_and_definitions import ItemMod
from file_management import FilesManager, DataPath
from shared.trade_item_enums import ModClass


def _vectorize_mod(mod_str: str, max_mods: int, possible_values: int):
    vectored = dict()
    for mod_i in list(range(max_mods)):
        vectored[f'{mod_str}_id_{mod_i}'] = None

        for value_i in list(range(possible_values)):
            vectored[f'{mod_str}_id_{mod_i}_value_{value_i}'] = None

    return vectored


class VectorizedAttributes:

    def __init__(self,
                 max_implicit_mods: int = 6,
                 max_fractured_mods: int = 18,
                 max_
                 max_values_per_mod: int = 6):

        self.num_mods = {
            ModClass.IMPLICIT: 0,
            ModClass.EXPLICIT: 0,
            ModClass.ENCHANT: 0,
            ModClass.FRACTURED: 0
        }

        def add_mod(mod: ItemMod):
            num_mods = self.num_mods[mod.mod_class]
            max_mods = self.max_mods[mod.mod_class]
            if num_mods == self.max_mods[mod.mod_class]:
                raise RuntimeError(f"Attempted to add mod # {num_mods + 1} to vectorized attributes"
                                   f"when max is {max_mods}.")

            max_values = self.max_values[mod.mod_class]
            if len(mod.)


class ModConverter:

    def __init__(self):
        files_manager = FilesManager()
        self.encode_to_mod_id = files_manager.file_data[DataPath.MOD_ENCODES]
        self.mod_id_to_encode = {mod_id: encode_id for encode_id, mod_id in self.encode_to_mod_id.items()}

        self.vector = VectorizedAttributes()

    def vectorize_mods(self, mods: list[ItemMod]):
        for i, mod in enumerate(mods):
            if mod.mod_id not in self.mod_id_to_encode:
                new_encode_id = len(self.encode_to_mod_id)
                self.encode_to_mod_id[new_encode_id] = mod.mod_id
                self.mod_id_to_encode[mod.mod_id] = new_encode_id



