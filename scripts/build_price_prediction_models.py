
from file_management import FilesManager
from price_predict_ai_model import PricePredictModelPipeline
from psql import PostgreSqlManager

files_manager = FilesManager()
psql_manager = PostgreSqlManager()

pipeline = PricePredictModelPipeline(files_manager=files_manager,
                                     psql_manager=psql_manager)
pipeline.run()
