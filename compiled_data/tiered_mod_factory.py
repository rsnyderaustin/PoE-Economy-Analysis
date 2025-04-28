
from external_apis import OfficialModsManager, CoEModsManager
from things import TieredMod


class TieredModFactory:

    @classmethod
    def create_tiered_mods(cls,
                           official_mods_manager: OfficialModsManager,
                           coe_mods_manager: CoEModsManager) -> set[TieredMod]:
        official_mod_texts = official_mods_manager.mod_texts
        coe_mod_texts = coe_mods_manager.mod_texts

        tiered_mods = set()

        for coe_mod_text in coe_mod_texts:
            paired_official_mod_texts = []
            if coe_mod_text in official_mod_texts:
                pass



