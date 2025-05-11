import pandas as pd

from file_management import FileKey, FilesManager
from program_manager import ProgramManager
from poecd_api import PoecdDataPuller, PoecdEndpoint

poecd_m = PoecdDataPuller()
mod_data = poecd_m.pull_data(endpoint=PoecdEndpoint.STATS)
bases_data = poecd_m.pull_data(endpoint=PoecdEndpoint.BASES)

f_manager = FilesManager()
f_manager.file_data[FileKey.POECD_STATS] = mod_data
f_manager.file_data[FileKey.POECD_BASES] = bases_data

f_manager.save_data(keys=[FileKey.POECD_STATS, FileKey.POECD_BASES])

listings = FilesManager().file_data[FileKey.CRITICAL_PRICE_PREDICT_TRAINING]
prog_manager = ProgramManager()
prog_manager.fetch_training_data()
# prog_manager.build_price_predict_model()
prog_manager.find_underpriced_items()