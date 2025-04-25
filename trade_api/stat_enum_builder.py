
from dataclasses import dataclass
import logging
import inflect
import re
import requests


@dataclass
class StatEnum:
    stat_id: str
    stat_name: str

logging.info("Starting inflect engine.")
inflect_eng = inflect.engine()
logging.info("\tStarted inflect engine.")


def _create_stat_enum(entry: dict) -> StatEnum:
    def convert_to_word(match):
        number = int(match.group())
        return inflect_eng.number_to_words(number).upper()
    stat_id = entry['id']
    stat_name = entry['text']

    # Replace numbers with words
    cleaned_name = re.sub(r'\d+', convert_to_word, stat_name)

    # Filter out any non-letters and numbers
    cleaned_name = re.sub(r'[^a-zA-Z0-9\s]', '', cleaned_name)

    cleaned_name = (cleaned_name
                    .upper()
                    .replace(' ', '_')
                    .replace('__', '_')
                    .replace('\n', '_')
                    .replace('-', '_')
                    .lstrip('_')
                    )

    return StatEnum(
        stat_id=stat_id,
        stat_name=cleaned_name
    )


class StatEnumBuilder:

    """
        In theory this should only really ever be ran if there are stat attributes that are erroring or that are added in later.
        It just fetches the text required for creating a stat enum class
    """

    base_url = "https://www.pathofexile.com/api/trade/data/stats"
    headers = {
        'Accept': 'image/avif,image/webp,image/png,image/svg+xml,image/*;q=0.8,*/*;q=0.5',
        'Referer': 'https://www.pathofexile.com/api/trade/data/stats',
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) Gecko/20100101 Firefox/137.0"
    }

    acceptable_stat_types = [
        'pseudo',
        'explicit',
        'implicit',
        'enchant',
        'crafted'
    ]

    @classmethod
    def _fetch_stats_json(cls):
        response = requests.get(url=cls.base_url,
                                headers=cls.headers)
        response.raise_for_status()
        return response.json()

    @classmethod
    def _create_enums_blocks(cls):
        stats_json = cls._fetch_stats_json()

        stat_blocks = [
            stat_block for stat_block in stats_json['result']
            if stat_block['id'] in cls.acceptable_stat_types
        ]

        stats_returnable = dict()
        for stat_block in stat_blocks:
            block_id = stat_block['id']
            stats_returnable[block_id] = dict()

            entries = stat_block['entries']

            for entry in entries:
                stat_enum = _create_stat_enum(entry=entry)

                stats_returnable[block_id][stat_enum.stat_name] = stat_enum.stat_id

        return stats_returnable

    @classmethod
    def create_enum_file_text(cls):
        blocked_enums = cls._create_enums_blocks()

        returnable_text = 'from enum import Enum\n\nclass StatBlocks:\n'
        for block_name, enum_block in blocked_enums.items():
            returnable_text += f'\n\tclass {block_name.capitalize()}(Enum):'

            for enum_name, enum_value in enum_block.items():
                returnable_text += f'\n\t\t{enum_name.upper()} = "{enum_value}"'

        return returnable_text



