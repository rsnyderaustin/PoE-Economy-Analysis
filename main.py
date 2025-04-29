
import json
import logging
from pathlib import Path

from compiled_data import ApisCompiler

logging.basicConfig(level=logging.INFO)
logging.info("test")

compiler = ApisCompiler.compile()

json_path = '/external_apis/craft_of_exile_api/json_data/poecd_stats.json'
