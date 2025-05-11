import itertools
from instances_and_definitions import ModAffixType
from shared import shared_utils
from .data_management import PoecdMod, PoecdAtypeManager, PoecdSourceStore


class AtypesManagersFactory:

    def __init__(self, source_store):
        self.source_store = source_store

    def _create_tiers_data(self):
        socketer_mod_ids = {
            mod['id_modifier'] for mod in self.source_store.stats_data['modifiers']['seq']
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
            new_mod = PoecdMod(atype_id=atype_id,
                               atype_name=self.source_store.fetch_atype_name(atype_id),
                               mod_id=mod_id)
            mods.append(new_mod)

        return mods

    def _create_atypes_managers(self, tiers_data):
        atype_ids = set(
            atype_id
            for mod_id, atype_dict in tiers_data.items()
            for atype_id in atype_dict.keys()
        )
        # Updating this with these valid Atype IDs just for good measure
        atype_ids.update(self.source_store.valid_atype_ids)

        atypes_managers = [
            PoecdAtypeManager(atype_id=atype_id,
                              atype_name=self.source_store.fetch_atype_name(atype_id=atype_id))
            for atype_id in atype_ids
        ]
        return atypes_managers

    def _fill_atype_managers_with_mods(self, mods, atype_managers):
        managers_dict = {manager.atype_id: manager for manager in atype_managers}

        for mod in mods:
            atype_manager = managers_dict[mod.atype_id]
            atype_manager.add_mod(mod)

    def _fill_mods_with_tiers(self, mods, tiers_data):
        mods_dict = {(mod.atype_id, mod.mod_id): mod for mod in mods}

        inputs = [
            (mod_id, atype_id, tiers_data)
            for mod_id, atype_dict in tiers_data.items()
            for atype_id, tier_data in atype_dict.items()
            if atype_id in self.source_store.valid_atype_ids
        ]

        for mod_id, atype_id, tier_data in inputs:
            mod = mods_dict[(atype_id, mod_id)]
            mod.add_tier(tier_data=tier_data)

    def build_mods_managers(self) -> list[PoecdAtypeManager]:

        tiers_data = self._create_tiers_data()

        mods = self._create_mods(tiers_data=tiers_data)
        atype_managers = self._create_atypes_managers(tiers_data=tiers_data)
        self._fill_atype_managers_with_mods(mods=mods, atype_managers=atype_managers)
        self._fill_mods_with_tiers(mods=mods, tiers_data=tiers_data)
        
        # Create mods
        mods = list()
        for atype_id, mod_ids in atype_to_mods.items():
            for mod_id in mod_ids:
                mod_text = source_store.mod_id_to_text[mod_id]
                mod_text = shared_utils.sanitize_mod_text(mod_text)
                mod_types = source_store.mod_id_to_mod_types[mod_id]
                affix_type = source_store.mod_id_to_affix_type[mod_id]
                if affix_type and affix_type == 'prefix':
                    affix_type = ModAffixType.PREFIX
                elif affix_type and affix_type == 'suffix':
                    affix_type = ModAffixType.SUFFIX

                new_mod = PoecdMod(
                    atype_id=atype_id,
                    atype_name=self.atype_id_to_atype_name[atype_id],
                    mod_id=mod_id,
                    mod_text=mod_text,
                    mod_types=mod_types,
                    affix_type=affix_type,
                    tiers_list=tiers_lists[atype_id][mod_id]
                )
                mods.append(new_mod)

        return mods