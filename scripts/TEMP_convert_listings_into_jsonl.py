
import ijson
import json

from pathlib import Path

input_path = Path("raw_listings.json")       # Your big list-of-dicts file
output_path = Path("raw_listings.jsonl")     # Output as JSON Lines

with open(input_path, 'r', encoding='utf-8') as infile, \
     open(output_path, 'w', encoding='utf-8') as outfile:

    # ijson.items() streams individual dicts from the top-level list
    for item in ijson.items(infile, 'item'):
        json.dump(item, outfile)
        outfile.write('\n')