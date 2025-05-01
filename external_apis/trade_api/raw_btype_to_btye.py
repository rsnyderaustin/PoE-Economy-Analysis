

class RawATypeToAType:

    _convertable_raw_atypes = {
        'Body Armour', 'Boots', 'Gloves', 'Helmet', 'Shield'
    }

    @classmethod
    def convert(cls,
                raw_atype: str,
                str_requirement: int,
                int_requirement: int,
                dex_requirement: int):
        if raw_atype in cls._convertable_raw_atypes:
            if dex_requirement:
                if int_requirement:
                    return f"{raw_atype} DEX/INT"

                if str_requirement:
                    return f"{raw_atype} STR/DEX"

                return f"{raw_atype} DEX"

            if int_requirement:
                if str_requirement:
                    return f"{raw_atype} STR/INT"

                return f"{raw_atype} INT"

            if str_requirement:
                return f"{raw_atype} STR"
        else:
            return raw_atype
