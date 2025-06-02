
import ijson
import json
from pathlib import Path

from file_management.file_managers import CustomEncoder

input_path = Path.cwd() / "file_management/dynamic_files/raw_listings.json"       # Your big list-of-dicts file
output_path = Path.cwd() / "file_management/dynamic_files/raw_listings.jsonl"       # Output as JSON Lines

with open(input_path, 'r', encoding='utf-8') as infile, open(output_path, 'w', encoding='utf-8') as outfile:

    # ijson.items() streams individual dicts from the top-level list
    for item in ijson.items(infile, 'item'):
        json.dump(item, outfile, cls=CustomEncoder)
        outfile.write('\n')