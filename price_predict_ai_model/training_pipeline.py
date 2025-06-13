import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split

from data_transforming import ListingsTransforming
from file_management.file_managers import PricePredictModelFiles, PricePredictCacheFile
from price_predict_ai_model import visuals
from program_logging import LogFile, LogsHandler
from psql import PostgreSqlManager
from shared.dataframe_prep import DataFramePrep
from .stats_prep import StatsPrep

price_predict_log = LogsHandler().fetch_log(LogFile.PRICE_PREDICT_MODEL)


class ModelPerformance:

    def __init__(self,
                 atype: str,
                 tier: str):
        self.atype = atype
        self.tier = tier

        # Params
        self.eta = None
        self.max_depth = None
        self.num_boost_rounds = None
        self.early_stopping_rounds = None

        # Results
        self.mse = None

class ModelPerformanceTracker:

    def __init__(self):
        self._performance_data = {}

    def add_model_performance(self, model_performance: ModelPerformance):
        for k, v in model_performance.__dict__:
            if k not in self._performance_data:
                self._performance_data[k] = v

            self._performance_data[k].append(v)

class PricePredictModelPipeline:
    def __init__(self,
                 price_predict_files: PricePredictModelFiles,
                 psql_manager: PostgreSqlManager):
        self._files_manager = price_predict_files
        self._psql_manager = psql_manager

        self.should_plot_visuals = None

        self.model = None

        self._perf_tracker = ModelPerformanceTracker()

    def run(self,
            should_plot_visuals,
            from_cache: bool = False):
        self.should_plot_visuals = should_plot_visuals

        training_cache = PricePredictCacheFile()
        model_df = None
        if from_cache:
            model_df = training_cache.load(default=None)

            if model_df is None:
                print("Raw training cache data is missing / empty.")

        if model_df is None:
            print("Fetching PSQL table data.")
            raw_data = self._psql_manager.fetch_table_data(table_name='listings')

            print("Converting PSQL table to PricePredict DataFrame.")
            model_df = ListingsTransforming.to_price_predict_df(rows=raw_data)

            training_cache.save(model_df)

        for atype, atype_df in model_df.groupby('atype'):
            print(f"Beginning stats preparation for Atype {atype}")
            df_preps = StatsPrep.prep(df=atype_df, price_column='divs')

            print(f"Building PricePredict models for Atype {atype}")

            for tier, df_prep in df_preps.items():
                print(f" -------- Model for tier: {tier} -----------")
                performance_track = ModelPerformance(atype=atype,
                                                     tier=tier)
                self._train_model(df_prep=df_prep,
                                  performance_track=performance_track)

                self._perf_tracker.add_model_performance(performance_track)

            # self._files_manager.save_model(atype=atype, model=model)

    def _train_model(self,
                     performance_track: ModelPerformance,
                     df_prep: DataFramePrep,
                     training_depth: int = 12,
                     eta: float = 0.00075,
                     num_boost_rounds: int = 1250):
        """Train the XGBoost model on the input dataframe."""
        train_x, test_x, train_y, test_y = train_test_split(
            df_prep.features,
            df_prep.log_price_column,
            test_size=0.2,
            random_state=42
        )

        train_data = xgb.DMatrix(train_x, label=train_y, enable_categorical=True)
        test_data = xgb.DMatrix(test_x, label=test_y, enable_categorical=True)

        params = {
            'max_depth': training_depth,
            'eta': eta,
            'eval_metric': 'rmse'
        }
        performance_track.eta = eta
        performance_track.max_depth = training_depth
        performance_track.num_boost_rounds = num_boost_rounds

        evals = [(train_data, 'train'), (test_data, 'test')]

        print("Training model.")
        early_stopping_rounds = 50
        self.model = xgb.train(
            params,
            train_data,
            num_boost_round=num_boost_rounds,
            early_stopping_rounds=early_stopping_rounds,
            evals=evals,
            # Uncomment below to use custom objective
            # obj=lambda preds, dmatrix: self._prediction_penalty_objective(preds, dmatrix, overprediction_weight, underprediction_weight),
            verbose_eval=False
        )
        performance_track.early_stopping_rounds = early_stopping_rounds

        print("Evaluating model.")
        """Evaluate the model's prediction performance."""
        test_predictions = self.model.predict(test_data)

        # Only do this if the price column is logged
        # Exponentiate to reverse the earlier log transformation (return to original price scale)
        test_predictions = np.expm1(test_predictions)
        test_y = np.expm1(test_y)

        mse = mean_squared_error(test_y, test_predictions)
        performance_track.mse = mse
        print(f"Atype {performance_track.atype} MSE: {mse}")

        return self.model
