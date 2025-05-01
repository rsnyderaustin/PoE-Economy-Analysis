
from external_apis.trade_api.things.skill import Skill


class SkillsCreator:

    @classmethod
    def create_skills(cls, skills_dicts):
        skills = []
        for skill_dict in skills_dicts:
            raw_skill = skill_dict['values'][0]

            if isinstance(raw_skill, str):
                _, level_str, *skill_parts = raw_skill.split()
                level = int(level_str)
                skill_name = ' '.join(skill_parts)
            else:
                skill_name = raw_skill[0][0]
                level = raw_skill[0][1]

            new_skill = Skill(
                skill_name=skill_name,
                skill_level=level
            )

            skills.append(new_skill)

        return skills


