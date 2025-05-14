import logging

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import xgboost as xgb
from sklearn.model_selection import train_test_split

from file_management import FilesManager, FileKey
from price_predict_model import utils


def lowest_price_focused_error(y_true, y_pred):
    """
    Custom error metric that:
    - Strongly penalizes overpredictions (predicted price > true price).
    - Lightly penalizes underpredictions (predicted price < true price).
    - Optionally ignores prices above a threshold (e.g., outlier listings).

    Args:
        y_true: Array of true (lowest observed) prices.
        y_pred: Array of predicted prices.

    Returns:
        Gradient and Hessian for XGBoost/LightGBM.
    """
    # Penalty weights (tune these)
    overprediction_penalty = 2.0  # Heavy penalty for overpredicting
    underprediction_penalty = 0.1  # Light penalty for underpredicting

    error = y_pred - y_true

    # Gradient calculation
    grad = np.where(
        error > 0,
        overprediction_penalty * error,  # Overprediction → large gradient
        underprediction_penalty * error  # Underprediction → small gradient
    )

    # Hessian (constant for simplicity, but can be tuned)
    hess = np.ones_like(y_true) * 0.1  # Adjust for stability

    return grad, hess


def custom_objective(preds: np.ndarray,
                     dmatrix: xgb.DMatrix,
                     overprediction_weight: float,
                     underprediction_weight: float) -> tuple[np.ndarray, np.ndarray]:
    """XGBoost-compatible objective focusing on lowest prices."""
    y_true = dmatrix.get_label()  # Extract true labels from DMatrix

    error = preds - y_true
    grad = np.where(error > 0, overprediction_weight * error, underprediction_weight * error)
    hess = np.ones_like(y_true) * 0.1  # Constant hessian for stability

    return grad, hess


def _apply_log_outliers(row):
    non_null_dict = {col: val for col, val in row.items()
                     if pd.notna(val) and val > 0.0 and col not in ['Predicted Price', 'exalts']}

    print(f"\n\n")
    print(f"Predicted Price: {row['Predicted Price']}"
          f"\nActual Price: {row['exalts']}"
          f"\n\tAttributes and values:")

    for k, v in non_null_dict.items():
        print(f"\t{k}: {v}")


def log_outliers(outliers_df):
    outliers_df.apply(_apply_log_outliers, axis=1)


def _plot_correlation_matrix(df: pd.DataFrame):
    corr_df = df.select_dtypes(include=['int64', 'float64'])
    plt.figure(figsize=(18, 8))
    corr_matrix = corr_df.corr()
    sns.heatmap(corr_matrix[['exalts']].sort_values(by='exalts', ascending=False), annot=True, cmap='coolwarm')
    plt.show()


def _plot_exalts_histogram(df: pd.DataFrame):
    df['exalts'].hist()
    plt.show()


def _plot_feature_importance(model, atype: str):
    importance = model.get_score(importance_type='weight')

    # Create a DataFrame for easier plotting
    importance_df = pd.DataFrame(list(importance.items()), columns=['Feature', 'Importance'])
    importance_df = importance_df.sort_values(by='Importance', ascending=False)

    # Plot the feature importances
    importance_df.plot(kind='barh', x='Feature', y='Importance', legend=False, figsize=(10, 6))
    plt.title(f'Feature Importance for {atype}')
    plt.xlabel('Importance')
    plt.ylabel('Feature')
    plt.show()


def _plot_actual_vs_predicted(atype, test_predictions, test_targets):
    plt.figure(figsize=(8, 5))
    plt.scatter(test_predictions, test_targets, alpha=0.5)
    plt.plot([0, 4000], [0, 4000], color='red', linestyle='--')
    plt.xlabel("Predicted Price (Exalts)")
    plt.ylabel("Actual Prices (Exalts)")

    plt.title(f"Actual vs. Predicted Prices for {atype}")
    plt.grid(True)
    plt.show()


def _print_outliers(test_target_df: pd.DataFrame,
                    test_features_df: pd.DataFrame,
                    test_predictions):
    training_df = pd.concat([test_target_df, test_features_df], axis=1)
    training_df['Predicted Price'] = test_predictions

    # Add a column for the absolute error
    training_df['Absolute Error'] = (training_df['Predicted Price'] - training_df['exalts']).abs()

    under_priced_df = training_df[training_df['exalts'] - training_df['Predicted Price'] < 0]

    # Sort the dataframe by the absolute error in descending order
    outliers_df = under_priced_df.sort_values(by='Absolute Error', ascending=False).head(3)
    log_outliers(outliers_df)


def build_price_predict_model(df: pd.DataFrame,
                              atype: str,
                              overprediction_weight: float = 2.0,
                              underprediction_weight: float = 0.1,
                              training_depth: int = 12,
                              eta: float = 0.00075,
                              num_boost_rounds: int = 1250):
    """
    Builds an XGBoost price prediction model with custom loss weighting.
    """

    # _plot_correlation_matrix(df)

    # Split features and target variable
    features = df.drop(columns=['exalts'], errors='ignore')
    target_col = df['exalts']

    # Train/test split
    training_feat, test_feat, training_target, test_target = train_test_split(
        features, target_col, test_size=0.2, random_state=42
    )

    # Convert to DMatrix format for XGBoost
    train_data = xgb.DMatrix(training_feat, label=training_target, enable_categorical=True)
    test_data = xgb.DMatrix(test_feat, label=test_target, enable_categorical=True)

    # Log model parameters
    logging.info(f"Depth: {training_depth}, ETA: {eta}, Boost rounds: {num_boost_rounds}")

    # Model parameters
    params = {
        'max_depth': training_depth,
        'eta': eta,
        'eval_metric': 'rmse'
    }

    evals = [(train_data, 'train'), (test_data, 'test')]

    # Train XGBoost model
    model = xgb.train(
        params, train_data,
        num_boost_round=num_boost_rounds,
        early_stopping_rounds=50,
        evals=evals,
        obj=lambda preds, dmatrix: custom_objective(
            preds, dmatrix, overprediction_weight, underprediction_weight
        ),
        verbose_eval=False
    )

    # Cache trained model
    FilesManager().file_data[FileKey.PRICE_PREDICT_MODEL] = model

    # Evaluate performance
    test_predictions = model.predict(test_data)
    mse = utils.weighted_mse(test_target, test_predictions,
                             overprediction_weight=overprediction_weight,
                             underprediction_weight=underprediction_weight)

    logging.info(f"Weighted Mean Squared Error: {mse}")

    """_print_outliers(test_target_df=test_target,
                    test_features_df=test_feat,
                    test_predictions=test_predictions)"""

    # Get feature importance
    _plot_feature_importance(atype=atype, model=model)

    _plot_actual_vs_predicted(atype=atype,
                              test_predictions=test_predictions,
                              test_targets=test_target)

    return model

