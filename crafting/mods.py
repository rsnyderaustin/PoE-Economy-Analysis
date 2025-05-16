from file_management import FilesManager, FileKey
from instances_and_definitions import ItemMod, ModAffixType


def _distribute_mods(mods: list[ItemMod]):
    mods_dict = dict()
    for mod in mods:
        if mod.atype not in mods_dict:
            mods_dict[mod.atype] = dict()

        if mod.mod_id not in mods_dict[mod.atype]:
            mods_dict[mod.atype][mod.mod_id] = dict()

        mods_dict[mod.atype][mod.mod_id][mod.mod_ilvl] = mod

    return mods_dict


class ModsManager:
    """
    This is a mods manager built only for the RL crafting environment.
    """

    def __init__(self):
        files_manager = FilesManager()
        self.mods_data = _distribute_mods(mods=files_manager.file_data[FileKey.MODS])

    def fetch_mod_tiers(self,
                        atype: str,
                        max_ilvl: int,
                        force_mod_type: str = None,
                        exclude_mod_ids: set[str] = None,
                        affix_types: list[ModAffixType] = None) -> list[ItemMod]:
        atype_mods = self.mods_data[atype]

        if exclude_mod_ids:
            atype_mods = {mod_id: mod_data for mod_id, mod_data in atype_mods.items()
                          if mod_id not in exclude_mod_ids}

        if force_mod_type:
            atype_mods = {mod_id: mod_data for mod_id, mod_data in atype_mods.items()
                          if force_mod_type in mod_data.mod_types}

        if affix_types:
            atype_mods = {mod_id: mod_data for mod_id, mod_data in atype_mods.items()
                          if mod_data.affix_type and mod_data.affix_type in affix_types}

        atype_mods = [item_mod
                      for mod_id, mod_data in atype_mods.items()
                      for mod_ilvl, item_mod in mod_data.items()
                      if mod_ilvl <= max_ilvl]

        return atype_mods
