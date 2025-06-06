
print("Entered Python file for fill_training_data.py")

import program_logging

import psql
from operations_coordination.populate_training_data import TrainingDataPopulator
from file_management.file_managers import RawListingsFile

program_logging.basicConfig(level=program_logging.INFO)

print("Loading PSQL manager.")
psql_m = psql.PostgreSqlManager(skip_sql=False)

file = RawListingsFile()
populator = TrainingDataPopulator(psql_manager=psql_m)
populator.fill_training_data(file)

