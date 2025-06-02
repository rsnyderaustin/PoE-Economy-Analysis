
import logging
import psutil
import os

import psql
from file_management import FilesManager
from operations_coordination.populate_training_data import TrainingDataPopulator

logging.basicConfig(level=logging.INFO)

fm = FilesManager()
psql_manager = psql.PostgreSqlManager(skip_sql=False)

tdp = TrainingDataPopulator(files_manager=fm,
                            psql_manager=psql_manager)

tdp.fill_training_data()
