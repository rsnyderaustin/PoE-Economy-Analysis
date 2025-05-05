

class ATypeClassifier:

    _convertable_raw_atypes = {
        'Body Armour', 'Boots', 'Gloves', 'Helmet', 'Shield'
    }

    @classmethod
    def classify(cls,
                 item_data: dict = None,
                 raw_atype: str = None,
                 str_requirement: int = None,
                 int_requirement: int = None,
                 dex_requirement: int = None):
        """

        :param item_data: Either the item data alone or ALL other attributes should be supplied. Designed this way so that
            item atype can be easily determined outside of listing_creator
        :param raw_atype:
        :param str_requirement:
        :param int_requirement:
        :param dex_requirement:
        :return:
        """

        if item_data['baseType'] in ['Volatile Wand']:
            return 'Fire Wand'
        elif item_data['baseType'] in ['Withered Wand']:
            return 'Chaos Wand'
        elif item_data['baseType'] in ['Bone Wand']:
            return 'Physical Wand'
        elif item_data['baseType'] in ['Frigid Wand']:
            return 'Cold Wand'
        elif item_data['baseType'] in ['Galvanic Wand']:
            return 'Lightning Wand'

        if item_data and 'properties' in item_data and 'name' in item_data['properties'][0]:
            raw_atype = item_data['properties'][0]['name']

            # Sometimes the item's btype is surrounded by brackets, sometimes it's a string. I don't know why.
            if raw_atype.startswith('[') and raw_atype.endswith(']'):
                raw_atype = raw_atype[1:-1]

            # For weapon types that can be one- or two-handed, there is a pipe '|' that we need to handle
            if '|' in raw_atype:
                raw_atype = raw_atype.split('|', 1)[1]

        if raw_atype not in cls._convertable_raw_atypes:
            return raw_atype

        if item_data and 'requirements' in item_data:
            for req_dict in item_data['requirements']:
                if 'Str' in req_dict['name']:
                    str_requirement = int(req_dict['values'][0][0])
                if 'Int' in req_dict['name']:
                    int_requirement = int(req_dict['values'][0][0])
                if 'Dex' in req_dict['name']:
                    dex_requirement = int(req_dict['values'][0][0])

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

        return raw_atype
