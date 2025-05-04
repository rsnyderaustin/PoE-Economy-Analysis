
from shared import shared_utils


mod_class_to_abbrev = {
    'implicitMods': 'implicit',
    'enchantMods': 'enchant',
    'explicitMods': 'explicit',
    'fracturedMods': 'fractured',
    'runeMods': 'rune'
}


def determine_mod_id_to_mod_text(mod_class: ModClass, item_data: dict, sanitize_text: bool = False) -> dict:
    abbrev_class = mod_class_to_abbrev[mod_class]

    if abbrev_class not in item_data['extended']['hashes']:
        return dict()

    hashes_list = item_data['extended']['hashes'][abbrev_class]

    mod_id_display_order = [mod_hash[0] for mod_hash in hashes_list]
    mod_text_display_order = item_data[mod_class.value]

    mod_id_to_text = {
        mod_id: mod_text
        for mod_id, mod_text in list(zip(mod_id_display_order, mod_text_display_order))
    }
    if sanitize_text:
        return {
            mod_id: shared_utils.sanitize_mod_text(mod_text) for mod_id, mod_text in mod_id_to_text.items()
        }

    return mod_id_to_text

