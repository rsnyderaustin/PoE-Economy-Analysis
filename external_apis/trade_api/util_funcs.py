

class RawBtypeToBtype:

    _convertable_raw_btypes = {
        'Body Armour', 'Boots', 'Gloves', 'Helmet', 'Shield'
    }

    @classmethod
    def convert(cls,
                raw_btype: str,
                str_requirement: int,
                int_requirement: int,
                dex_requirement: int):
        if raw_btype in cls._convertable_raw_btypes:
            if dex_requirement:
                if int_requirement:
                    return f"{raw_btype} DEX/INT"

                if str_requirement:
                    return f"{raw_btype} STR/DEX"

                return f"{raw_btype} DEX"

            if int_requirement:
                if str_requirement:
                    return f"{raw_btype} STR/INT"

                return f"{raw_btype} INT"

            if str_requirement:
                return f"{raw_btype} STR"
        else:
            return raw_btype
