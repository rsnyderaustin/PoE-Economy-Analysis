import json
from pathlib import Path

from program_manager import ProgramManager
import pandas as pd

from shared import PathProcessor

training_data_json_path = (
            PathProcessor(Path.cwd())
            .attach_file_path_endpoint('xgboost_model/test_training_data.json')
            .path
        )
with open(training_data_json_path, 'r') as training_data_file:
    training_data = json.load(training_data_file)

df = pd.DataFrame(training_data)

prog_manager = ProgramManager()
prog_manager.execute()
