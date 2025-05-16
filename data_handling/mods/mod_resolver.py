import logging

import file_management
import poecd_api
from data_handling import utils
from file_management import FileKey
from instances_and_definitions import ModClass, utils as instance_utils, ItemMod
from shared import ATypeClassifier
from data_handling import mods
from data_handling.instance_variable_factories import ModFactory


class ModResolver:

    def __init__(self, global_atypes_manager: poecd_api.GlobalAtypesManager):
        self.files_manager = file_management.FilesManager()
        self.file_item_mods = self.files_manager.file_data[FileKey.MODS] or dict()

        poecd_attribute_finder = mods.PoecdAttributeFinder(global_atypes_manager=global_atypes_manager)
        self.mod_factory = ModFactory(poecd_attribute_finder)

    def _mod_is_valid(self, mod_data: dict):
        """
        This currently only applies to a blank implicit mod on spears
        """
        return not (len(mod_data['name']) == 0 and len(mod_data['tier']) == 0 and not mod_data['magnitudes'])

    def process_mods(self, item_data: dict) -> list[ItemMod]:
        """
        Attempts to pull each mod in the item's data from file. Otherwise, it manages the mod's creation and caching
        :return: All mods from the item data
        """
        mods = []

        atype = ATypeClassifier.classify(item_data)

        mod_class_enums = [e for e in ModClass if e != ModClass.RUNE if e.value in item_data]
        for mod_class_enum in mod_class_enums:
            mod_id_to_text = utils.determine_mod_id_to_mod_text(item_data=item_data,
                                                                mod_class_enum=mod_class_enum,
                                                                sanitize_text=False)
            abbrev_class = utils.abbreviate_mod_class(mod_class_enum)

            mods_data = item_data['extended']['mods'][abbrev_class]
            valid_mods_data = [mod_data for mod_data in mods_data if self._mod_is_valid(mod_data)]

            for mod_data in valid_mods_data:
                mod_ids = set(magnitude['hash'] for magnitude in mod_data['magnitudes'])
                affix_type = utils.determine_mod_affix_type(mod_data)
                mod_id = instance_utils.generate_mod_id(atype=atype, mod_ids=mod_ids, affix_type=affix_type)

                if mod_id in self.file_item_mods:
                    mods.append(self.file_item_mods[mod_id])
                    continue

                logging.info(f"Could not find mod with ID {mod_id}. Creating and caching.")
                new_mod = self.mod_factory.create_item_mod(mod_data=mod_data,
                                                           mod_id_to_text=mod_id_to_text,
                                                           mod_class=mod_class_enum,
                                                           atype=atype)
                self.file_item_mods[new_mod.mod_id] = new_mod  # Add the new mod to our mod JSON file
                mods.append(new_mod)

        return mods



