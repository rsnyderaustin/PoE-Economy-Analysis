from file_management.file_managers import PricePredictModelFiles
from price_predict_ai_model import PricePredictModelPipeline
from psql import PostgreSqlManager

psql_manager = PostgreSqlManager(skip_sql=False)

pipeline = PricePredictModelPipeline(price_predict_files=PricePredictModelFiles(),
                                     psql_manager=psql_manager)
pipeline.run(should_plot_visuals=True,
             from_cache=True)
