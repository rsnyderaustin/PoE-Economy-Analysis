

from operations_coordination.populate_training_data import TrainingDataPopulator
from file_management import FilesManager, DataPath

fm = FilesManager()
responses = fm.file_data[DataPath.RAW_LISTINGS]

tdp = TrainingDataPopulator(refresh_poecd_source=True,
                            testing=True)

tdp.fill_training_data(responses)
