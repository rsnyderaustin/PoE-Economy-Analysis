
print("Entered Python file for fill_training_data.py")

import logging

import psql
from file_management import FilesManager
from operations_coordination.populate_training_data import TrainingDataPopulator

logging.basicConfig(level=logging.INFO)

fm = FilesManager()

print("Loading PSQL manager.")
psql_manager = psql.PostgreSqlManager(skip_sql=False)

print("Loading TrainingDataPopulator class object.")
tdp = TrainingDataPopulator(files_manager=fm,
                            psql_manager=psql_manager)

print("Starting TrainingDataPopulator.fill_training_data function")
tdp.fill_training_data()
