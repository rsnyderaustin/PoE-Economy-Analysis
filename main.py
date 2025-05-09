import json
from pathlib import Path

import pandas as pd

from file_management import FilesManager, FileKeys
from program_manager import ProgramManager
from shared import PathProcessor

prog_manager = ProgramManager()
# build_xgboost()
prog_manager.build_price_predict_model()
