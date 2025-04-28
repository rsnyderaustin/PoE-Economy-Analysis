
import logging
import re

from items.attributes import Mod, Skill


class AttributeFactory:
    range_regex = '(\d+)\s+to\s+(\d+)'
    single_number_regex = '[+-]?\d+'

    @classmethod
    def create_mod(cls, raw_string: str) -> Mod:
        range_match = re.match(cls.range_regex, raw_string)
        if range_match:
            if len(range_match.groups()) >= 2:
                logging.error(f"Found more than one range match for raw mod '{raw_string}'")

            range_groups = range_match.groups()
            range_min, range_max = float(range_groups[0]), float(range_groups[1])

            cleaned_string = re.sub(cls.range_regex, '# to #', raw_string)

            mod = Mod(
                numeric_values=[(range_min, range_max)],
                mod_string=cleaned_string
            )
            return mod

        values = re.findall(cls.single_number_regex, raw_string)
        values = list(map(float, values))

        cleaned_string = re.sub(cls.single_number_regex, '#', raw_string)

        mod = Mod(
            numeric_values=values,
            mod_string=cleaned_string
        )

        return mod

    @classmethod
    def create_skill(cls, raw_string) -> Skill:
        match = re.match(r'Level\s+(\d+)\s+(.+)', raw_string)
        num_matches = len(match.groups())

        if match and num_matches == 2:
            level = int(match.group(1))  # Captures the number
            skill = match.group(2)  # Captures the skill string
            skill = Skill(
                skill_name=skill,
                level=level
            )
            return skill
        else:
            logging.error(f"Unable to create skill from raw skill mod '{raw_string}'")

