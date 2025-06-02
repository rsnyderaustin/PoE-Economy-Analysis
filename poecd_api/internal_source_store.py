
from shared import shared_utils
from shared.enums.item_enums import AType


def _convert_str_to_int(s):
    if isinstance(s, str) and (s.isdigit() or (s.startswith('-') and s[1:].isdigit())):
        return int(s)
    return s


def _numify_dict(obj):
    if isinstance(obj, dict):
        new_dict = {}
        for k, v in obj.items():
            new_key = _convert_str_to_int(k)
            new_dict[new_key] = _numify_dict(v)
        return new_dict
    elif isinstance(obj, list):
        return [_numify_dict(item) for item in obj]
    else:
        return _convert_str_to_int(obj)


class PoecdSourceStore:
    def __init__(self, bases_data, stats_data):
        self.bases_data = _numify_dict(bases_data)
        self.bases_data = shared_utils.sanitize_dict_texts(self.bases_data)

        self.stats_data = _numify_dict(stats_data)
        self.stats_data = shared_utils.sanitize_dict_texts(self.stats_data)

        self._mod_id_to_text = self.bases_data['mod']
        self._mod_id_to_affix_type = self._build_mod_id_to_affix_type()
        self._atype_id_to_atype_name = self.bases_data['base']
        self.valid_atype_ids = set(self._atype_id_to_atype_name.keys())

        self._mod_id_to_mod_types = self._build_mod_id_to_mod_types()

    def _build_mod_id_to_affix_type(self) -> dict:
        return {
            mod_data_dict['id_modifier']: mod_data_dict['affix']
            for mod_data_dict in self.stats_data['modifiers']['seq']
        }

    @staticmethod
    def _determine_mod_types(mtypes_string: str) -> list:
        if not mtypes_string:
            return []
        parsed = [int(part) for part in mtypes_string.split('|') if part]
        return parsed

    def _build_mod_id_to_mod_types(self) -> dict:
        mod_type_id_to_mod_type = {
            mod_type_dict['id_mtype']: mod_type_dict['name_mtype']
            for mod_type_dict in self.stats_data['mtypes']['seq']
        }

        mod_id_to_mod_type_ids = {
            mod_data['id_modifier']: self._determine_mod_types(mod_data['mtypes'])
            for mod_data in self.stats_data['modifiers']['seq']
        }

        return {
            mod_id: [mod_type_id_to_mod_type[mod_type_id] for mod_type_id in mod_type_ids]
            for mod_id, mod_type_ids in mod_id_to_mod_type_ids.items()
        }

    def fetch_mod_text(self, mod_id) -> str | None:
        return self._mod_id_to_text.get(mod_id, None)

    def fetch_affix_type(self, mod_id) -> str | None:
        return self._mod_id_to_affix_type.get(mod_id, None)

    def fetch_atype(self, atype_id) -> AType | None:
        atype_name = self._atype_id_to_atype_name[atype_id]
        return AType(atype_name)

    def fetch_mod_types(self, mod_id) -> list[str] | None:
        return self._mod_id_to_mod_types.get(mod_id, None)
