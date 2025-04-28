
import logging

import craft_of_exile_api

class CraftOfExileToOfficialPoe:

    def __init__(self, coe_compiler: craft_of_exile_api.Compiler, official_mod_data: dict):

        mod_name_to_official_info = dict()
        for mod_class, mods_list in official_mod_data.items():
            for mod_data_dict in mods_list:
                official_id = mod_data_dict['id']
                mod_text = mod_data_dict['text'].lower()
                mod_type = mod_data_dict['type']

                mod_name_to_official_info[mod_text] = {
                    'id': official_id,
                    'type': mod_type
                }

        coe_mod_text_to_id = coe_compiler.mod_id_by_mod_text
        for coe_mod_text, coe_mod_id in coe_mod_text_to_id.items():
            if coe_mod_text not in mod_name_to_official_info:
                logging.info(f"Could not find CoE mod text {coe_mod_text} in official PoE data.")

    @classmethod
    def _coe_mod_id_to_official_id(cls, mod_id: str):
        pass
