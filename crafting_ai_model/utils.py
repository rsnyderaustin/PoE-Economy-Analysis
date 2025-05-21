
def format_mods_into_dict(mods):
    return [
        {
            'mod_id': mod.mod_id,
            'mod_affix_type': mod.affix_type.value,
            'sub_mod_values': [sub_mod.actual_values for sub_mod in mod.sub_mods]
        } for mod in mods
    ]


def format_skills_into_dict(skills):
    return [
        {
            'name': skill.name,
            'level': skill.level
        } for skill in skills
    ]
