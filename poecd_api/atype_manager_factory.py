from shared import shared_utils
from shared.enums.item_enums import ModAffixType
from .internal_source_store import PoecdSourceStore
from .mods_management import PoecdMod, AtypeModsManager


class AtypeManagerFactory:

    def __init__(self, source_store: PoecdSourceStore):
        self.source_store = source_store

    def _create_tiers_data(self):
        socketer_mod_ids = {
            int(mod['id_modifier']) for mod in self.source_store.stats_data['modifiers']['seq']
            if mod['affix'] == 'socket'
        }

        tiers_data = {
            mod_id: atype_data for mod_id, atype_data in self.source_store.stats_data['tiers'].items()
            if mod_id not in socketer_mod_ids
        }

        return tiers_data

    def _create_mods(self, tiers_data) -> list[PoecdMod]:
        mods = []
        inputs = [
            (mod_id, atype_id)
            for mod_id, atype_dict in tiers_data.items()
            for atype_id in atype_dict.keys()
        ]
        for mod_id, atype_id in inputs:
            affix_type_str = self.source_store.fetch_affix_type(mod_id)
            affix_type = ModAffixType.PREFIX if affix_type_str == 'prefix' else ModAffixType.SUFFIX
            mod_text = shared_utils.sanitize_mod_text(self.source_store.fetch_mod_text(mod_id))
            new_mod = PoecdMod(atype_id=atype_id,
                               atype_name=self.source_store.fetch_atype_name(atype_id),
                               mod_id=mod_id,
                               mod_text=mod_text,
                               mod_types=self.source_store.fetch_mod_types(mod_id=mod_id),
                               affix_type=affix_type)
            mods.append(new_mod)

        return mods

    def _create_atypes_managers(self, mods):
        atype_ids = set(mod.atype_id for mod in mods)
        atype_id_to_mods = {atype_id: set() for atype_id in atype_ids}
        for mod in mods:
            atype_id_to_mods[mod.atype_id].add(mod)

        atypes_managers = [
            AtypeModsManager(atype_id=atype_id,
                             atype_name=self.source_store.fetch_atype_name(atype_id=atype_id),
                             mods=atype_id_to_mods[atype_id])
            for atype_id in atype_ids
        ]
        return atypes_managers

    def _fill_mods_with_tiers(self, mods, tiers_data):
        mods_dict = {(mod.atype_id, mod.mod_id): mod for mod in mods}

        inputs = [
            (mod_id, atype_id, tiers_data)
            for mod_id, atype_dict in tiers_data.items()
            for atype_id, tier_data_list in atype_dict.items()
            for tiers_data in tier_data_list
            if atype_id in self.source_store.valid_atype_ids
        ]

        for mod_id, atype_id, tier_data in inputs:
            mod = mods_dict[(atype_id, mod_id)]
            mod.add_tier(tier_data=tier_data)

    def build_mods_managers(self) -> list[AtypeModsManager]:

        tiers_data = self._create_tiers_data()

        mods = self._create_mods(tiers_data=tiers_data)
        atype_managers = self._create_atypes_managers(mods=mods)
        self._fill_mods_with_tiers(mods=mods, tiers_data=tiers_data)

        return atype_managers
