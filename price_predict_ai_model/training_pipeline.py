import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split

from data_transforming import ListingsTransforming
from file_management import PricePredictModelFiles
from price_predict_ai_model import visuals
from psql import PostgreSqlManager
from shared import env_loader
from shared.logging import LogFile, LogsHandler
from stat_analysis.stats_prep import StatsPrep

price_predict_log = LogsHandler().fetch_log(LogFile.PRICE_PREDICT_MODEL)


class PricePredictModelPipeline:
    def __init__(self,
                 price_predict_files: PricePredictModelFiles,
                 psql_manager: PostgreSqlManager,
                 should_plot_visuals=False):
        self._files_manager = price_predict_files
        self.psql_manager = psql_manager

        self.should_plot_visuals = should_plot_visuals

        self.model = None

    @staticmethod
    def _prediction_penalty_objective(y_true, y_pred, overpredict_penalty=2.0, underpredict_penalty=0.1):
        """Custom error function for diagnostic use (not directly used in training)."""
        error = y_pred - y_true
        grad = np.where(error > 0, overpredict_penalty * error, underpredict_penalty * error)
        hess = np.ones_like(y_true) * 0.1
        return grad, hess

    def run(self, plot_visuals=False):
        self.should_plot_visuals = plot_visuals

        table_name = env_loader.get_env("PSQL_TRAINING_TABLE")
        raw_data = self.psql_manager.fetch_table_data(table_name)
        model_df = ListingsTransforming.to_price_predict_df(rows=raw_data)

        for atype, atype_df in model_df.groupby('atype'):
            atype_df = StatsPrep.prep_dataframe(df=atype_df, price_column='divs')

            if atype_df is None:
                continue

            model = self._train_model(
                df=atype_df,
                atype=str(atype),
                price_column='divs'
            )

            self._files_manager.save_model(atype=atype, model=model)

    def _train_model(self,
                     df: pd.DataFrame,
                     price_column: str,
                     atype: str,
                     price_is_logged=False,
                     training_depth: int = 12,
                     eta: float = 0.00075,
                     num_boost_rounds: int = 1250):
        """Train the XGBoost model on the input dataframe."""
        features_df = df.drop(columns=[price_column], errors='ignore')
        target_col = df[price_column]

        train_x, test_x, train_y, test_y = train_test_split(
            features_df, target_col, test_size=0.2, random_state=42
        )

        train_data = xgb.DMatrix(train_x, label=train_y, enable_categorical=True)
        test_data = xgb.DMatrix(test_x, label=test_y, enable_categorical=True)

        params = {
            'max_depth': training_depth,
            'eta': eta,
            'eval_metric': 'rmse'
        }

        evals = [(train_data, 'train'), (test_data, 'test')]

        self.model = xgb.train(
            params,
            train_data,
            num_boost_round=num_boost_rounds,
            early_stopping_rounds=50,
            evals=evals,
            # Uncomment below to use custom objective
            # obj=lambda preds, dmatrix: self._prediction_penalty_objective(preds, dmatrix, overprediction_weight, underprediction_weight),
            verbose_eval=False
        )

        self._evaluate_model(test_data=test_data,
                             test_y=test_y,
                             test_x=test_x,
                             features_df=features_df,
                             atype=atype,
                             price_is_logged=price_is_logged)

        return self.model

    def _evaluate_model(self, test_data, test_y, test_x, features_df, atype, price_is_logged):
        """Evaluate the model's prediction performance."""
        test_predictions = self.model.predict(test_data)

        if price_is_logged:
            # Exponentiate to reverse the earlier log transformation (return to original price scale)
            test_predictions = np.expm1(test_predictions)
            test_y = np.expm1(test_y)

        test_results_df = pd.DataFrame({
            'test_y': test_y,
            'test_predictions': test_predictions,
            'error': np.where(test_predictions != 0,
                              (test_y - test_predictions).abs() / test_predictions,
                              np.nan)
        })
        test_results_df = pd.concat([test_results_df, features_df], axis=1)
        test_results_df.sort_values(by='error')

        mse = mean_squared_error(test_y, test_predictions)
        price_predict_log.info(f"Atype {atype} MSE: {mse}")

        if self.should_plot_visuals:
            visuals.plot_feature_importance(model=self.model, atype=atype)
            visuals.plot_actual_vs_predicted(atype, test_predictions, test_y)

