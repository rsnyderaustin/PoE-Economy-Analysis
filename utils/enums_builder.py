
import re
from dataclasses import dataclass

import requests

from .funcs import create_enum_name


@dataclass
class NewEnum:
    enum_name: str
    enum_value: str


def _create_enum(entry: dict) -> NewEnum | None:

    if not entry['id'] or not entry['text']:
        return None

    enum_value = entry['id']
    enum_name = entry['text']

    return NewEnum(
        enum_name=create_enum_name(enum_name),
        enum_value=enum_value
    )


class EnumsBuilder:

    """
        In theory this should only really ever be ran if there are erroring enum blocks or enums that need added.
        It just fetches the text required for creating an enum class
    """

    base_url = "https://www.pathofexile.com/api/trade2/data/"
    headers = {
        'Accept': 'image/avif,image/webp,image/png,image/svg+xml,image/*;q=0.8,*/*;q=0.5',
        'Referer': 'FILL_IN_WITH_BASE_URL',
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) Gecko/20100101 Firefox/137.0"
    }

    @classmethod
    def _fetch_stats_json(cls, url_endpoint: str):
        base_url = f"{cls.base_url}/{url_endpoint}"

        # Split once at '://'
        protocol, url = base_url.split('://', 1)

        # Fix only the "rest" part
        url = re.sub(r'/+', '/', url)

        base_url = f"{protocol}://{url}"
        headers = {
            **cls.headers,
            'Referer': base_url
        }
        response = requests.get(url=base_url,
                                headers=headers)
        response.raise_for_status()
        return response.json()

    @classmethod
    def _create_enums_blocks(cls, stats_json: dict):
        enum_blocks = [
            enum_block for enum_block in stats_json['result']
        ]

        enums_returnable = dict()
        for enum_block in enum_blocks:
            if not enum_block['entries']:
                continue

            block_id = enum_block['id']

            enums_returnable[block_id] = dict()

            entries = enum_block['entries']

            for entry in entries:
                new_enum = _create_enum(entry=entry)

                # Returns None if either the name or value are not present
                if not new_enum:
                    continue

                enums_returnable[block_id][new_enum.enum_name] = new_enum.enum_value

        return enums_returnable

    @classmethod
    def create_enum_file_text(cls, super_class_name: str, url_endpoint: str):
        stats_json = cls._fetch_stats_json(url_endpoint=url_endpoint)
        blocked_enums = cls._create_enums_blocks(stats_json=stats_json)

        returnable_text = f'from enum import Enum\n\nclass {super_class_name}:\n'
        for block_name, enum_block in blocked_enums.items():
            returnable_text += f'\n\tclass {block_name.capitalize()}(Enum):'

            for enum_name, enum_value in enum_block.items():
                returnable_text += f'\n\t\t{enum_name.upper()} = "{enum_value}"'

        return returnable_text



