
from data_handling.api_response_parser import ApiResponseParser
from shared.enums import ItemCategory


class ATypeClassifier:

    _classifiable_item_categories = {
        ItemCategory.BODY_ARMOUR, ItemCategory.BOOTS, ItemCategory.GLOVES, ItemCategory.HELMET, ItemCategory.SHIELD
    }

    _wand_btype_map = {
        'volatile_wand': 'fire_wand',
        'withered_wand': 'chaos_wand',
        'bone_wand': 'physical_wand',
        'frigid_wand': 'cold_wand',
        'galvanic_wand': 'lightning_wand',
    }

    @classmethod
    def classify(cls, rp: ApiResponseParser):
        cat = rp.item_category

        if rp.item_btype in cls._wand_btype_map:
            return cls._wand_btype_map[rp.item_btype]

        # Bucklers are just classified as a dex shield in Poecd
        cat = ItemCategory.SHIELD if rp.item_category == ItemCategory.BUCKLER else cat

        if cat not in cls._classifiable_item_categories:
            return rp.item_category.value

        str_requirement = rp.str_requirement if rp.str_requirement else 1 if 'armour' in rp.item_properties else 0
        int_requirement = rp.int_requirement if rp.int_requirement else 1 if 'energy_shield' in rp.item_properties else 0
        dex_requirement = rp.dex_requirement if rp.dex_requirement else 1 if 'evasion' in rp.item_properties else 0

        if dex_requirement:
            if int_requirement:

                return f"{cat.value}_(dex/int)"

            if str_requirement:
                return f"{cat.value}_(str/dex)"

            return f"{cat.value}_(dex)"

        if int_requirement:
            if str_requirement:
                return f"{cat.value}_(str/int)"

            return f"{cat.value}_(int)"

        if str_requirement:
            return f"{cat.value}_(str)"

        raise ValueError(f"Could not determine Stat type for item {rp.item_name} with category {cat.value}")
