from src.market_item_analysis.file_management.file_managers import PricePredictModelFiles, PricePredictPerformanceFile
from src.market_item_analysis.price_predict_ai_model import PricePredictModelPipeline
from src.market_item_analysis.psql import PostgreSqlManager

psql_manager = PostgreSqlManager(skip_sql=True)

pipeline = PricePredictModelPipeline(price_predict_files=PricePredictModelFiles(),
                                     performance_file=PricePredictPerformanceFile(),
                                     psql_manager=psql_manager)
pipeline.run(load_model_from_cache=True)
