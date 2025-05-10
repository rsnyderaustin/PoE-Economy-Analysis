import pandas as pd

from file_management import FileKey, FilesManager
from program_manager import ProgramManager

prog_manager = ProgramManager()
prog_manager.fetch_training_data()
# prog_manager.build_price_predict_model()
prog_manager.find_underpriced_items()