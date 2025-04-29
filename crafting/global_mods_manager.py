
from compiled_data import BaseItemTypeModsManager
from utils.enums import ModAffixType


class GlobalModsManager:

    def __init__(self, base_item_type_mods_managers: list[BaseItemTypeModsManager]):
        self._base_item_type_to_mods_manager = {
            mods_manager.base_type_name: mods_manager
            for mods_manager in base_item_type_mods_managers
        }

    def fetch_mods_and_tiers(self,
                             base_item_type_name: str,
                             ilvl: int,
                             affix_types: list[ModAffixType],
                             force_mod_type: ModAffixType = None,
                             ignore_mod_ids: set[int] = None) -> list[CompiledModWithTiers]:
        base_item_type_mod_manager = self._base_item_type_to_mods_manager[base_item_type_name]
        mods_with_tiers = base_item_type_mod_manager.fetch_mods(
            ilvl=ilvl,
            affix_types=affix_types,
            force_mod_type=force_mod_type,
            ignore_mod_ids=ignore_mod_ids
        )
        return mods_with_tiers


