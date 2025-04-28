


class ModDetails:

    def __init__(self, mod_id: str, mod_name: str, api_tiers_data: dict):
        self.mod_id = mod_id
        self.mod_name = mod_name

        self.tiers_data_by_base_type_id = dict()
        for mod_id, tiers_data_by_base_type_id in api_tiers_data.items():
            for base_type_id, tiers_data_list in tiers_data_by_base_type_id.items():
                if base_type_id not in self.tiers_data_by_base_type_id:
                    self.tiers_data_by_base_type_id[base_type_id] = list()
                for tiers_data in tiers_data_list:
                    mod_tier = ModTier(
                        mod_id=mod_id,
                        ilvl_requirement = tiers_data['ilvl'],
                        values_range=tiers_data['nvalues'],
                        weighting=tiers_data['weighting']
                    )
                    self.tiers_data_by_base_type_id[base_type_id].append(mod_tier)
        x=0


class Compiler:

    def __init__(self, mods_data: dict, bases_data: dict):
        # Body Armour (DEX), Claw, Crossbow, etc
        self.base_type_by_base_type_id = bases_data['base']

        # Boots, Gloves, Body Armours, Charms, Flasks, etc
        self.base_group_by_base_group_id = bases_data['bgroup']

        self.mod_text_by_mod_id = {
            mod_id: mod_text.lower().lstrip('+').lstrip('-')
            for mod_id, mod_text in bases_data['mod'].items()
        }
        self.mod_id_by_mod_text = {v: k for k, v in self.mod_text_by_mod_id.items()}
        self.base_item_name_by_base_item_id = bases_data['bitem']
        self.socketer_name_by_socketer_id = bases_data['socketable']

        self.mod_ids_by_base_type_id = mods_data['basemods']
        # Armour: ['5', '6', etc],
        # Weapons: ['11', '12', etc]
        self.socketaable_id_by_item_class = mods_data['socketables']['bybase']

        # I think this right but not sure
        self.mod_type_by_mod_type_id = {
            mod_type_dict['id_mtype']: mod_type_dict['name_mtype']
            for mod_type_dict in mods_data['mtypes']['seq']
        }
