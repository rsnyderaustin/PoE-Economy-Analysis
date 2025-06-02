
print("Entered Python file for fill_training_data.py")

import logging

import psql
from file_management import FilesManager
from operations_coordination.populate_training_data import TrainingDataPopulator

logging.basicConfig(level=logging.INFO)

fm = FilesManager()

print("Loading PSQL manager.")
psql_m = psql.PostgreSqlManager(skip_sql=False)
