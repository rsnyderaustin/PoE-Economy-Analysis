
from instances_and_definitions import ModAffixType
from shared import shared_utils


class PoecdMod:

    def __init__(self,
                 atype_id: str,
                 atype_name: str,
                 mod_id: int,
                 mod_text: str = None,
                 mod_types: list[str] = None,
                 affix_type: ModAffixType = None):
        self.atype_id = atype_id
        self.atype_name = atype_name
        self.mod_id = mod_id
        self.mod_text = mod_text

        self.mod_types = mod_types or []
        self.affix_type = affix_type

        self.ilvl_to_mod_tier = dict()

    def __hash__(self):
        return hash(f"{self.mod_id}_{self.atype_name}_{self.affix_type.value}")

    def add_tier(self, tier_data):
        ilvl = tier_data['ilvl']
        self.ilvl_to_mod_tier[ilvl] = tier_data

    def fetch_weighting(self, ilvl: str):
        return self.ilvl_to_mod_tier[ilvl]['weighting']


class PoecdAtypeManager:

    def __init__(self,
                 atype_id: str,
                 atype_name: str,
                 mods: set[PoecdMod]):
        self.atype_id = atype_id
        self.atype_name = atype_name
        self.mods = mods

        self._mod_id_to_mod = {mod.mod_id: mod for mod in mods}
        self._mod_text_to_mod = {mod.mod_text: mod for mod in mods}

        self._mods_affixed_dict = {
            ModAffixType.PREFIX: {mod.mod_text: mod for mod in mods if mod.affix_type == ModAffixType.PREFIX},
            ModAffixType.SUFFIX: {mod.mod_text: mod for mod in mods if mod.affix_type == ModAffixType.SUFFIX}
        }

        # This is useful for when we are matching mods to the Trade API data
        self.hybrid_parts_to_parent_dict = self._create_hybrid_to_parent_dict()
        self.hybrid_parts_to_parent_affixed_dict = {
            ModAffixType.PREFIX: self._create_hybrid_to_parent_dict(affix_type=ModAffixType.PREFIX),
            ModAffixType.SUFFIX: self._create_hybrid_to_parent_dict(affix_type=ModAffixType.SUFFIX)
        }
        self.num_hybrid_parts_dict = {
            mod.mod_id: len(mod.mod_text.split(','))
            for mod in mods
        }

        self.mod_id_to_affix_type = {mod.mod_id: mod.affix_type for mod in mods}
        self.mod_id_to_text = {mod.mod_id: mod.mod_text for mod in mods}
        self.mod_text_to_id = {v: k for k, v in self.mod_id_to_text.items()}

    def fetch_mod(self, mod_text: str, affix_type: ModAffixType):
        return self._mods_affixed_dict[affix_type][mod_text]

    def fetch_mod_by_id(self, mod_id: str):
        return self._mod_id_to_mod[mod_id]

    def _create_hybrid_to_parent_dict(self, affix_type: ModAffixType = None) -> dict:
        hybrid_part_to_parent_id = dict()
        for mod in self.mods:
            if affix_type and mod.affix_type != affix_type:
                continue
            if ',' in mod.mod_text:
                hybrid_parts = [
                    part.strip()
                    for part in mod.mod_text.split(',')
                ]
                for part in hybrid_parts:
                    if part not in hybrid_part_to_parent_id:
                        hybrid_part_to_parent_id[part] = set()
                    hybrid_part_to_parent_id[part].add(mod.mod_id)
        return hybrid_part_to_parent_id


class PoecdSourceStore:
    def __init__(self, bases_data, stats_data):
        self.bases_data = bases_data
        self.stats_data = stats_data

        self._mod_id_to_text = bases_data['mod']
        self._mod_id_to_affix_type = self._build_mod_id_to_affix_type()
        self._atype_id_to_atype_name = bases_data['base']
        self.valid_atype_ids = set(self._atype_id_to_atype_name.keys())

        self._mod_id_to_mod_types = self._build_mod_id_to_mod_types()

    def _build_mod_id_to_affix_type(self) -> dict:
        return {
            mod_data_dict['id_modifier']: mod_data_dict['affix']
            for mod_data_dict in self.stats_data['modifiers']['seq']
        }

    def _build_mod_id_to_mod_types(self) -> dict:
        mod_type_id_to_mod_type = {
            mod_type_dict['id_mtype']: mod_type_dict['name_mtype']
            for mod_type_dict in self.stats_data['mtypes']['seq']
        }

        mod_id_to_mod_type_ids = {
            mod_data['id_modifier']: shared_utils.parse_poecd_mtypes_string(mod_data['mtypes'])
            for mod_data in self.stats_data['modifiers']['seq']
        }

        return {
            mod_id: [mod_type_id_to_mod_type[mod_type_id] for mod_type_id in mod_type_ids]
            for mod_id, mod_type_ids in mod_id_to_mod_type_ids.items()
        }

    def fetch_mod_text(self, mod_id) -> str | None:
        return self._mod_id_to_text.get(mod_id, None)

    def fetch_affix_type(self, mod_id) -> str | None:
        return self._mod_id_to_affix_type.get(mod_id, None)

    def fetch_atype_name(self, atype_id) -> str | None:
        return self._atype_id_to_atype_name.get(atype_id, None)

    def fetch_mod_types(self, mod_id) -> str | None:
        return self._mod_id_to_mod_types.get(mod_id, None)


class GlobalAtypesManager:

    def __init__(self, atype_managers: list[PoecdAtypeManager]):
        self._atypes_managers_by_id = {am.atype_id: am for am in atype_managers}
        self._atypes_managers_by_name = {am.atype_name: am for am in atype_managers}

    def fetch_atype_manager(self, atype_id: str = None, atype_name: str = None):
        if atype_id:
            return self._atypes_managers_by_id[atype_id]
        elif atype_name:
            return self._atypes_managers_by_name[atype_name]
        else:
            raise ValueError(f"Did receive an argument for function {__name__}")

