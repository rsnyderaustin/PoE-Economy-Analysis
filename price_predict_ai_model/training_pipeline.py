import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split

from data_transforming import ListingsTransforming
from file_management.file_managers import PricePredictModelFiles, PricePredictCacheFile, PricePredictPerformanceFile
from program_logging import LogFile, LogsHandler
from psql import PostgreSqlManager
from price_predict_ai_model.dataframe_prep import DataFramePrep
from .stats_prep import StatsPrep
from .utils import ModelLifeCycle

price_predict_log = LogsHandler().fetch_log(LogFile.PRICE_PREDICT_MODEL)


class PricePredictModelPipeline:
    def __init__(self,
                 price_predict_files: PricePredictModelFiles,
                 performance_file: PricePredictPerformanceFile,
                 psql_manager: PostgreSqlManager):
        self._files_manager = price_predict_files
        self._performance_file = performance_file
        self._psql_manager = psql_manager

        self.model = None

        self._model_lifecycles = []

    def _load_training_data(self, from_cache: bool) -> pd.DataFrame:
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

        return model_df

    def _stratify_dataframe(self, model_df: pd.DataFrame):
        stratified_dfs = {}

        for atype, atype_df in model_df.groupby('atype'):
            prep = DataFramePrep(atype_df, price_col_name='divs')
            stratified = prep.stratify_dataframe(
                col_name='divs',
                quantiles=[0.25, 0.5, 0.75, 0.9, 1.0]
            )

            tier_names = [
                'very_low_price',
                'low_price',
                'med_price',
                'high_price',
                'very_high_price'
            ]

            for tier_name, df in zip(tier_names, stratified):
                stratified_dfs[(atype, tier_name)] = df

        return stratified_dfs

    def _combine_lifecycles(self) -> pd.DataFrame:
        cols = {c: [] for c in self._model_lifecycles[0].__dict__}
        for ml in self._model_lifecycles:
            for c, v in ml.__dict__.items():
                cols[c].append(v)
        return pd.DataFrame(cols)

    def run(self,
            load_model_from_cache: bool = False):
        model_df = self._load_training_data(from_cache=load_model_from_cache)
        model_df['days_since_league_start'] = (model_df['minutes_since_league_start'] / (60 * 24)).astype(int)

        stratified_dfs = self._stratify_dataframe(model_df)

        for (atype, tier), df in stratified_dfs.items():
            model_lifecycle = ModelLifeCycle(atype=str(atype),
                                             tier=str(tier))
            self._model_lifecycles.append(model_lifecycle)

            print(f"Beginning stats preparation for Atype {atype}")
            df_prep = StatsPrep.prep(model_lifecycle=model_lifecycle,
                                     df=df,
                                     price_column='divs')

            self._train_model(df_prep=df_prep,
                              model_lifecycle=model_lifecycle)

            # self._files_manager.save_model(atype=atype, model=model)

        perf_df = self._combine_lifecycles()
        self._performance_file.save(perf_df)

    def _train_model(self,
                     model_lifecycle: ModelLifeCycle,
                     df_prep: DataFramePrep,
                     training_depth: int = 12,
                     eta: float = 0.00075,
                     num_boost_rounds: int = 1250,
                     early_stopping_rounds: int = 50):
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
        model_lifecycle.eta = eta
        model_lifecycle.max_depth = training_depth
        model_lifecycle.num_boost_rounds = num_boost_rounds

        evals = [(train_data, 'train'), (test_data, 'test')]

        print("Training model.")
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
        model_lifecycle.early_stopping_rounds = early_stopping_rounds

        print("Evaluating model.")
        """Evaluate the model's prediction performance."""
        test_predictions = self.model.predict(test_data)

        # Only do this if the price column is logged
        # Exponentiate to reverse the earlier log transformation (return to original price scale)
        test_predictions = np.expm1(test_predictions)
        test_y = np.expm1(test_y)

        mse = mean_squared_error(test_y, test_predictions)
        model_lifecycle.mse = mse
        print(f"Atype {model_lifecycle.atype} tier {model_lifecycle.tier} MSE: {mse}")

        return self.model
