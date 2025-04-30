
from .mods_management import BtypeModsManager, CompiledMod, CompiledModWithTiers
from utils.enums import ModAffixType


class GlobalBtypesManager:

    def __init__(self, btype_mods_managers: list[BtypeModsManager]):
        self._btype_to_mods_manager = {
            mods_manager.btype_name: mods_manager
            for mods_manager in btype_mods_managers
        }

    def fetch_btype_mod_manager(self, btype_name: str):
        return self._btype_to_mods_manager[btype_name]

    def fetch_mods_and_tiers(self,
                             btype_name: str,
                             ilvl: int,
                             affix_types: list[ModAffixType],
                             force_mod_type: ModAffixType = None,
                             ignore_mod_ids: set[int] = None) -> list[CompiledModWithTiers]:
        btype_mod_manager = self._btype_to_mods_manager[btype_name]
        mods_with_tiers = btype_mod_manager.fetch_mods(
            ilvl=ilvl,
            affix_types=affix_types,
            force_mod_type=force_mod_type,
            ignore_mod_ids=ignore_mod_ids
        )
        return mods_with_tiers


