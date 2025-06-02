
print("Entered Python file for fill_training_data.py")

import logging

import psql
from operations_coordination.populate_training_data import TrainingDataPopulator
from file_management import RawListingsFile

logging.basicConfig(level=logging.INFO)

print("Loading PSQL manager.")
psql_m = psql.PostgreSqlManager(skip_sql=False)

file = RawListingsFile()
populator = TrainingDataPopulator(psql_manager=psql_m)
populator.fill_training_data(file)

