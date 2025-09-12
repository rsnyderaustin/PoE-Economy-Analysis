from dataclasses import dataclass

from shared.enums.item_enums import ModAffixType, AType


def create_mod_id(atype: AType, mod_text: str, affix_type: ModAffixType):
    return atype.value, mod_text, affix_type.value


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
        return create_mod_id(atype=self.atype, mod_text=self.mod_text, affix_type=self.affix_type)

    def __hash__(self):
        return hash(self.mod_id)

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

    def __init__(self):
        self._mods = set()
        # This is useful for when we are matching mods to the Trade API data
        self._hybrid_parts_to_parents = dict()
        self._hybrid_parts_to_parents_affixed = {
            ModAffixType.PREFIX: dict(),
            ModAffixType.SUFFIX: dict()
        }
        self._mod_hybrid_parts = dict()

    def attempt_add_mod(self, mod: Poe2DbMod):
        if ',' not in mod.mod_text:
            return

        self._mod_hybrid_parts[mod] = mod.mod_text.split(',')

        hybrid_dict = self._hybrid_parts_to_parents
        hybrid_affix_dict = self._hybrid_parts_to_parents_affixed[mod.affix_type]
        hybrid_parts = [
            part.strip()
            for part in mod.mod_text.split(',')
        ]
        for part in hybrid_parts:
            if part not in hybrid_dict:
                hybrid_dict[part] = set()

            hybrid_dict[part].add(mod)

            if part not in hybrid_affix_dict:
                hybrid_affix_dict[part] = set()

            hybrid_affix_dict[part].add(mod)

    def fetch_hybrid_part_to_parents(self, affix_type: ModAffixType = None):
        if affix_type:
            return self._hybrid_parts_to_parents_affixed[affix_type]
        else:
            return self._hybrid_parts_to_parents

    def determine_number_of_hybrid_parts(self, mod: Poe2DbMod):
        return self._mod_hybrid_parts[mod]

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
                    hybrid_part_to_parent_id[part].add(mod.sub_mod_hash)
        return hybrid_part_to_parent_id


class AtypeModsManager:

    def __init__(self,
                 atype: AType):
        self.atype = atype
        self.mods = []

        self._mod_id_to_mod = dict()
        self._mod_text_to_mod = dict()

        self._mods_affixed_dict = {
            ModAffixType.PREFIX: dict(),
            ModAffixType.SUFFIX: dict()
        }

        self._hybrid_mod_analyzer = HybridModAnalyzer()

    @property
    def mod_texts(self) -> list[str]:
        return list(self._mod_text_to_mod.keys())

    def add_mod(self, mod: Poe2DbMod):
        if mod.mod_id in self._mod_id_to_mod:
            return

        self.mods.append(mod)
        self._mod_id_to_mod[mod.mod_id] = mod
        self._mod_text_to_mod[mod.mod_text] = mod
        self._mods_affixed_dict[mod.affix_type][mod.mod_text] = mod
        self._hybrid_mod_analyzer.attempt_add_mod(mod)

    def has_mod(self, mod_id):
        return mod_id in self._mod_id_to_mod

    def fetch_mod(self, mod_id):
        return self._mod_id_to_mod[mod_id]

    def fetch_mod_texts(self, affix_type: ModAffixType = None):
        if affix_type:
            return list(self._mods_affixed_dict[affix_type].keys())

        return list(self._mod_text_to_mod.keys())

    def fetch_hybrid_part_to_parents(self, affix_type: ModAffixType = None) -> dict[str: set[Poe2DbMod]]:
        return self._hybrid_mod_analyzer.fetch_hybrid_part_to_parents(affix_type)

    def determine_number_of_hybrid_parts(self, mod_id: Poe2DbMod):
        return self._hybrid_mod_analyzer.determine_number_of_hybrid_parts(mod_id)


class Poe2DbModsManager:

    def __init__(self, atype_managers: list[AtypeModsManager]):
        self._atypes_managers = {am.atype: am for am in atype_managers}

    def fetch_atype_manager(self, atype: AType = None):
        return self._atypes_managers[atype]
    
    def fetch_mod(self, atype: AType, mod_id: int):
        atype_manager = self._atypes_managers[atype]

        return atype_manager.fetch_mod(mod_id)
