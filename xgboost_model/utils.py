from instances_and_definitions import ModifiableListing


def sum_sub_mod_values(listing: ModifiableListing):
    summed_sub_mods = {}
    for mod in listing.mods:
        for sub_mod in mod.sub_mods:
            if sub_mod.actual_values:
                avg_value = sum(sub_mod.actual_values) / len(sub_mod.actual_values)
                if sub_mod.mod_id not in summed_sub_mods:
                    summed_sub_mods[sub_mod.mod_id] = avg_value
                else:
                    summed_sub_mods[sub_mod.mod_id] += avg_value
            else:
                # If there is no value then it's just a static property (ex: "You cannot be poisoned"), and so
                # we assign it a 1 to indicate to the model that it's an active mod
                summed_sub_mods[sub_mod.mod_id] = 1
    return summed_sub_mods


def count_socketers(listing: ModifiableListing) -> dict:
    socketer_counts = dict()
    for socketer_name in listing.socketers:
        if socketer_name not in socketer_counts:
            socketer_counts[socketer_name] = 0
        socketer_counts[socketer_name] += 1

    return socketer_counts

