import json
from pathlib import Path

import pandas as pd

from program_manager import ProgramManager
from shared import PathProcessor

# build_xgboost()

training_data_json_path = (
            PathProcessor(Path.cwd())
            .attach_file_path_endpoint('xgboost_model/training_data/listings.json')
            .path
        )
with open(training_data_json_path, 'r') as training_data_file:
    training_data = json.load(training_data_file)

df = pd.DataFrame(training_data)

prog_manager = ProgramManager()
prog_manager.execute()
