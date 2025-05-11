import data_handling
import file_management
from data_handling import utils
from file_management import FileKey
from instances_and_definitions import ModClass, utils as instance_utils, ItemMod
from shared import ATypeClassifier


class ResourceResolver:

    def __init__(self,
                 files_manager: file_management.FilesManager,
                 instance_var_constructor: data_handling.InstanceVariableConstructor):
        files_manager = files_manager
        self.instance_var_constructor = instance_var_constructor

        self.file_item_mods = files_manager.file_data[FileKey.ITEM_MODS]

    def _should_skip_mod(self, mod_data: dict):
        """
        This currently only applies to a blank implicit mod on spears
        """
        return len(mod_data['name']) == 0 and len(mod_data['tier']) == 0 and not mod_data['magnitudes']

    def _cache_mod(self, item_mod: ItemMod):
        self.file_item_mods[]

    def pull_mods(self, item_data: dict):
        mods = []

        atype = ATypeClassifier.classify(item_data)

        mod_class_enums = [e for e in ModClass if e != ModClass.RUNE if e.value in item_data]
        item_mod_classes = [utils.mod_class_to_abbrev[e.value]
                            for e in ModClass if e != ModClass.RUNE and e.value in item_data]
        for mod_class_enum in mod_class_enums:
            mod_id_to_text = utils.determine_mod_id_to_mod_text(item_data=item_data,
                                                                mod_class=mod_class_enum,
                                                                sanitize_text=False)
            abbrev_class = utils.mod_class_to_abbrev(mod_class_enum)

            mods_data = item_data['extended']['mods'][abbrev_class]
            valid_mods_data = [mod_data for mod_data in mods_data if not self._should_skip_mod(mod_data)]

            for mod_data in valid_mods_data:
                mod_ids = set(magnitude['hash'] for magnitude in mod_data['magnitudes'])
                affix_type = utils.determine_mod_affix_type(mod_data)
                mod_id = instance_utils.generate_mod_id(atype=atype,
                                                        mod_ids=mod_ids,
                                                        affix_type=affix_type)

                if mod_id in self.file_item_mods:
                    mods.append(self.file_item_mods[mod_id])
                    continue

                new_mod = self.instance_var_constructor.create_item_mod(mod_data=mod_data,
                                                                        mod_id_to_text=mod_id_to_text,
                                                                        mod_class=mod_class_enum,
                                                                        atype=atype)
                mods.append(new_mod)

        return mods



