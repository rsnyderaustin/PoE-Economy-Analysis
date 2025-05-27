
import logging

from operations_coordination.populate_training_data import TrainingDataPopulator
from file_management import FilesManager, DataPath

logging.basicConfig(level=logging.INFO)

fm = FilesManager()
responses = fm.fetch_data(data_path_e=DataPath.RAW_LISTINGS, default=[])

tdp = TrainingDataPopulator(refresh_poecd_source=True,
                            testing=False,
                            files_manager=fm)

tdp.fill_training_data()
