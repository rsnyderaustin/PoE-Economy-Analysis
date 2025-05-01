

class RawCategoryToCategory:

    _convertable_raw_categories = {
        'Body Armour', 'Boots', 'Gloves', 'Helmet', 'Shield'
    }

    @classmethod
    def convert(cls,
                raw_category: str,
                str_requirement: int,
                int_requirement: int,
                dex_requirement: int):
        if raw_category in cls._convertable_raw_categories:
            if dex_requirement:
                if int_requirement:
                    return f"{raw_category} DEX/INT"

                if str_requirement:
                    return f"{raw_category} STR/DEX"

                return f"{raw_category} DEX"

            if int_requirement:
                if str_requirement:
                    return f"{raw_category} STR/INT"

                return f"{raw_category} INT"

            if str_requirement:
                return f"{raw_category} STR"
        else:
            return raw_category
