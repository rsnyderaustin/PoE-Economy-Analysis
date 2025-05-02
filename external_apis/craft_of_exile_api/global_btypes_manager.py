
from compiled_data.mods_management import BtypeModsManager, CompiledModWithTiers
from utils.enums import ModAffixType


class GlobalBtypesManager:

    def __init__(self, btype_mods_managers: list[ATypeModsManager]):
        self._btype_to_mods_manager = {
            mods_manager.btype_name: mods_manager
            for mods_manager in btype_mods_managers
        }

    def fetch_btype_mod_manager(self, btype_name: str):
        return self._btype_to_mods_manager[btype_name]

    def fetch_mod_tiers(self,
                        atype_name: str,
                        ilvl: int,
                        affix_types: list[ModAffixType],
                        force_affix_type: ModAffixType = None,
                        ignore_mod_ids: set[int] = None) -> list[CompiledModWithTiers]:
        btype_mod_manager = self._btype_to_mods_manager[atype_name]
        mods_with_tiers = btype_mod_manager.fetch_mods(
            ilvl=ilvl,
            affix_types=affix_types,
            force_mod_type=force_affix_type,
            ignore_mod_ids=ignore_mod_ids
        )
        return mods_with_tiers

    def fetch_specific_mod_tiers(self,
                                 atype: str,
                                 ilvl: int,
                                 mod_ids: list[int]):
        atype_mod_manager = self._atype_to_mods_manager[atype]
        mod_tiers = atype_mod_manager.fetch_specific_mods(
            ilvl=ilvl,
            mod_ids=mod_ids
        )


