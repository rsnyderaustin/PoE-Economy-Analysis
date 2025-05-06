from instances_and_definitions import ModifiableListing, ItemMod


def _flatten_mod(item_mod: ItemMod):
    flattened_data = {
        'mod_tier': item_mod.mod_tier,
        'mod_ilvl': item_mod.mod_ilvl
    }

    sub_mod_values = dict()
    for sub_mod in item_mod.sub_mods:
        for i, values_range in enumerate(sub_mod.values_ranges):
            flattened_data[f"{sub_mod.mod_id}_{i}_min"] = values_range[0]
            flattened_data[f"{sub_mod.mod_id}_{i}_max"] = values_range[1]

def flatten_listing(listing: ModifiableListing):


