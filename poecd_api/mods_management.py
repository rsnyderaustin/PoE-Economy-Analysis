from dataclasses import dataclass

from shared.enums.item_enums import ModAffixType, AType


@dataclass
class PoeDbModTier:
    ilvl: int
    tier_name: str
    value_ranges: list[tuple]
    weighting: float


class Poe2DbMod:

    def __init__(self,
                 atype: AType,
                 affix_type: ModAffixType,
                 mod_text: str,
                 mod_types: list[str]):
        self.atype = atype
        self.affix_type = affix_type
        self.mod_text = mod_text
        self.mod_types = mod_types

        self.ilvl_to_mod_tier = dict()

    @property
    def mod_id(self) -> tuple:
        return self.create_mod_id(atype=self.atype, mod_text=self.mod_text)

    @staticmethod
    def create_mod_id(atype, mod_text):
        return atype, mod_text

    def __hash__(self):
        return self.mod_id

    def add_tier(self, ilvl: int, tier_name: str, value_ranges: list[tuple], weighting: float):
        self.ilvl_to_mod_tier[ilvl] = PoeDbModTier(
            ilvl=ilvl,
            tier_name=tier_name,
            value_ranges=value_ranges,
            weighting=weighting
        )

    def fetch_weighting(self, ilvl: int):
        mod_tier = self.ilvl_to_mod_tier[ilvl]
        return mod_tier.weighting


class HybridModAnalyzer:

    def __init__(self, mods: set[Poe2DbMod]):
        self._mods = mods
        # This is useful for when we are matching mods to the Trade API data
        self._hybrid_parts_to_parent_dict = self._create_hybrid_to_parent_dict()
        self._hybrid_parts_to_parent_affixed_dict = {
            ModAffixType.PREFIX: self._create_hybrid_to_parent_dict(affix_type=ModAffixType.PREFIX),
            ModAffixType.SUFFIX: self._create_hybrid_to_parent_dict(affix_type=ModAffixType.SUFFIX)
        }
        self._num_hybrid_parts_dict = {
            mod.mod_id: len(mod.mod_text.split(','))
            for mod in mods
        }

    def fetch_hybrid_to_parent_dict(self, affix_type: ModAffixType = None):
        if affix_type:
            return self._hybrid_parts_to_parent_affixed_dict[affix_type]
        else:
            return self._hybrid_parts_to_parent_dict

    def determine_number_of_hybrid_parts(self, mod_id: int):
        return self._num_hybrid_parts_dict[mod_id]

    def _create_hybrid_to_parent_dict(self, affix_type: ModAffixType = None) -> dict:
        hybrid_part_to_parent_id = dict()
        for mod in self._mods:
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


class AtypeModsManager:

    def __init__(self,
                 atype: AType,
                 mods: set[Poe2DbMod]):
        self.atype = atype
        self.mods = mods

        self._mod_id_to_mod = {mod.mod_id: mod for mod in mods}
        self._mod_text_to_mod = {mod.mod_text: mod for mod in mods}

        self._mods_affixed_dict = {
            ModAffixType.PREFIX: {mod.mod_text: mod for mod in mods if mod.affix_type == ModAffixType.PREFIX},
            ModAffixType.SUFFIX: {mod.mod_text: mod for mod in mods if mod.affix_type == ModAffixType.SUFFIX}
        }

        self.mod_id_to_affix_type = {mod.mod_id: mod.affix_type for mod in mods}
        self.mod_id_to_text = {mod.mod_id: mod.mod_text for mod in mods}
        self.mod_text_to_id = {v: k for k, v in self.mod_id_to_text.items()}

        self._hybrid_mod_analyzer = HybridModAnalyzer(mods=mods)

    @property
    def mod_texts(self) -> list[str]:
        return list(self.mod_text_to_id.keys())

    def fetch_mod(self, mod_text: str, affix_type: ModAffixType):
        return self._mods_affixed_dict[affix_type][mod_text]

    def fetch_mod_by_id(self, mod_id: int):
        return self._mod_id_to_mod[mod_id]

    def fetch_hybrid_parts_to_parent(self, affix_type: ModAffixType = None) -> dict:
        return self._hybrid_mod_analyzer.fetch_hybrid_to_parent_dict(affix_type)

    def determine_number_of_hybrid_parts(self, mod_id: int):
        return self._hybrid_mod_analyzer.determine_number_of_hybrid_parts(mod_id)


class Poe2DbModsManager:

    def __init__(self, atype_managers: list[AtypeModsManager]):
        self._atypes_managers = {am.atype: am for am in atype_managers}

    def fetch_atype_manager(self, atype: AType = None):
        return self._atypes_managers[atype]
    
    def fetch_mod(self, atype: AType, mod_text: str = None, affix_type: ModAffixType = None, mod_id: str = None):
        atype_manager = self._atypes_managers[atype]

        if mod_text and affix_type:
            mod = atype_manager.fetch_mod(mod_text, affix_type)
        else:
            mod = atype_manager.fetch_mod_by_id(mod_id)

        return mod
