

class ATypeClassifier:

    _convertable_raw_atypes = {
        'Body Armour', 'Boots', 'Gloves', 'Helmet', 'Shield'
    }

    @classmethod
    def classify(cls,
                 item_data: dict):

        base_type = item_data['baseType']

        if base_type in ['Volatile Wand']:
            return 'Fire Wand'
        elif base_type in ['Withered Wand']:
            return 'Chaos Wand'
        elif base_type in ['Bone Wand']:
            return 'Physical Wand'
        elif base_type in ['Frigid Wand']:
            return 'Cold Wand'
        elif base_type in ['Galvanic Wand']:
            return 'Lightning Wand'

        raw_atype = item_data['properties'][0]['name']

        # Sometimes the item's btype is surrounded by brackets, sometimes it's a string. I don't know why.
        if raw_atype.startswith('[') and raw_atype.endswith(']'):
            raw_atype = raw_atype[1:-1]

        # For weapon types that can be one- or two-handed, there is a pipe '|' that we need to handle
        if '|' in raw_atype:
            raw_atype = raw_atype.split('|', 1)[1]

        # Bucklers are just classified as a DEX shield in Poecd
        if raw_atype == 'Buckler':
            raw_atype = 'Shield'

        if raw_atype not in cls._convertable_raw_atypes:
            return raw_atype

        str_requirement = 0
        int_requirement = 0
        dex_requirement = 0
        if 'requirements' in item_data:
            for req_dict in item_data['requirements']:
                if 'Str' in req_dict['name']:
                    str_requirement = int(req_dict['values'][0][0])
                if 'Int' in req_dict['name']:
                    int_requirement = int(req_dict['values'][0][0])
                if 'Dex' in req_dict['name']:
                    dex_requirement = int(req_dict['values'][0][0])

        # This condition where we have no stat requirements seems to only happen when you have a Unique item that
        # has no stat requirements. In that case we just base the stat type off the requirements
        if not any([str_requirement, int_requirement, dex_requirement]):
            for property_ in item_data['properties']:
                if 'Armour' in property_['name']:
                    str_requirement = 1
                elif 'Energy Shield' in property_['name']:
                    int_requirement = 1
                elif 'Evasion' in property_['name']:
                    dex_requirement = 1

        if dex_requirement:
            if int_requirement:
                return f"{raw_atype} (DEX/INT)"

            if str_requirement:
                return f"{raw_atype} (STR/DEX)"

            return f"{raw_atype} (DEX)"

        if int_requirement:
            if str_requirement:
                return f"{raw_atype} (STR/INT)"

            return f"{raw_atype} (INT)"

        if str_requirement:
            return f"{raw_atype} (STR)"

        raise ValueError(f"Could not determine Stat type for item {item_data['baseType']}")
