import json
from pathlib import Path

import pandas as pd

from file_management import FilesManager, FileKeys
from program_manager import ProgramManager
from shared import PathProcessor

# build_xgboost()

prog_manager = ProgramManager()
prog_manager.execute()
