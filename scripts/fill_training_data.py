
import logging

from operations_coordination.populate_training_data import TrainingDataPopulator
from file_management import FilesManager, DataPath

logging.basicConfig(level=logging.INFO)

fm = FilesManager()
responses = fm.file_data[DataPath.RAW_LISTINGS]

tdp = TrainingDataPopulator(refresh_poecd_source=True,
                            testing=True,
                            files_manager=fm)

tdp.fill_training_data()
