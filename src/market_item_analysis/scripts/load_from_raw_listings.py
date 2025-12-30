
print("Entered Python file for fill_training_data.py")

from src.market_item_analysis import program_logging, psql
from src.market_item_analysis.file_management.file_managers import RawListingsFile
from src.market_item_analysis.operations_coordination.populate_training_data import TrainingDataPopulator

program_logging.basicConfig(level=program_logging.INFO)

print("Loading PSQL manager.")
psql_m = psql.PostgreSqlManager(skip_sql=False)

file = RawListingsFile()
populator = TrainingDataPopulator(psql_manager=psql_m)
populator.fill_training_data(file)

