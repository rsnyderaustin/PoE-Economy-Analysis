from things import CompiledMod, ModTier


class BaseItemTypeModsManager:

    def __init__(self, base_item_id: int, base_item_type: str):
        self.base_item_id = base_item_id
        self.base_item_type = base_item_type

        self._mod_id_to_mod = dict()
        self._mod_id_to_mod_tiers_data = dict()
        self._mod_type_to_mods = dict()

    def add_mod_tier(self,
                     base_type_id: int,
                     coe_mod_id: str,
                     mod: CompiledMod,
                     ilvl: int,
                     values_range: tuple,
                     weighting: float):
        for mod_type in mod.mod_types:
            if mod_type not in self._mod_type_to_mods:
                self._mod_type_to_mods[mod_type] = set()

            self._mod_type_to_mods[mod_type].add(mod)

        if mod.coe_mod_id not in self._mod_id_to_mod:
            self._mod_id_to_mod[mod.coe_mod_id] = mod

        if mod.coe_mod_id not in self._mod_id_to_mod_tiers_data:
            self._mod_id_to_mod_tiers_data[mod.coe_mod_id] = dict()

        self._mod_id_to_mod_tiers_data[mod.coe_mod_id][ilvl] = ModTier(
            base_type_id=base_type_id,
            coe_mod_id=coe_mod_id,
            ilvl=ilvl,
            values_range=values_range,
            weighting=weighting
        )
