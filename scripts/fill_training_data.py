
import logging

from file_management import FilesManager, DataPath
from operations_coordination.populate_training_data import TrainingDataPopulator
import psql

logging.basicConfig(level=logging.INFO)

fm = FilesManager()
responses = fm.fetch_data(data_path_e=DataPath.RAW_LISTINGS, default=[])
psql_manager = psql.PostgreSqlManager(skip_sql=True)

tdp = TrainingDataPopulator(refresh_poecd_source=True,
                            files_manager=fm,
                            psql_manager=psql_manager)

tdp.fill_training_data()
