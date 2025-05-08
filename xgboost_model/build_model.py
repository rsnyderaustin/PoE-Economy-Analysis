import itertools
import json
import logging
import random
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import xgboost as xgb
from sklearn.model_selection import train_test_split

from shared import PathProcessor
from xgboost_model import utils


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
    overprediction_penalty = 1.0  # Heavy penalty for overpredicting
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


def custom_objective(preds: np.ndarray, dmatrix: xgb.DMatrix) -> tuple[np.ndarray, np.ndarray]:
    """XGBoost-compatible objective focusing on lowest prices."""
    y_true = dmatrix.get_label()  # Extract true labels from DMatrix

    # Asymmetric penalties
    overprediction_penalty = 1.0  # Heavy penalty for overpredicting
    underprediction_penalty = 0.1  # Light penalty for underpredicting

    error = preds - y_true
    grad = np.where(error > 0, overprediction_penalty * error, underprediction_penalty * error)
    hess = np.ones_like(y_true) * 0.1  # Constant hessian for stability

    return grad, hess


def build_xgboost():
    logging.info("Beginning building XGBoost model.")
    training_data_json_path = (
        PathProcessor(Path.cwd())
        .attach_file_path_endpoint('xgboost_model/training_data/listings.json')
        .path
    )
    with open(training_data_json_path, 'r') as training_data_file:
        training_data = json.load(training_data_file)
    df = pd.DataFrame(training_data)
    """filter_cols = [
        'exalts',
        'days_since_listed',
        'open_prefixes',
        'open_suffixes',
        'atype',
        'Physical Damage',
        'Fire Damage',
        'Cold Damage',
        'Lightning Damage',
        'Chaos Damage',
        'Critical Hit Chance',
        'Attacks per Second',
        *[col for col in df.columns if 'Rune' in col or 'Soul Core' in col or 'Talisman' in col]
    ]
    missing_cols = [col for col in filter_cols if col not in df.columns]
    df = df[filter_cols]"""
    # df = df.drop(columns=['minutes_since_listed'])
    df['atype'] = df['atype'].astype("category")

    local_weapon_mods = [
        'adds_#_to_#_fire_damage',
        '#%_increased_attack_speed',
        '#%_increased_physical_damage',
        'adds_#_to_#_cold_damage',
        'adds_#_to_#_lightning_damage',
        'adds_#_to_#_physical_damage',
        '+#.#%_to_critical_hit_chance',
        '+#%_to_critical_hit_chance',
        '#% increased Physical Damage',
        'Adds # to # Fire Damage',
        'Adds # to # Lightning Damage',
        'Adds # to # Cold Damage',
        '#% increased Attack Speed',
        'Quality'
    ]
    df['pdps'] = df['Attacks per Second'] * df['Physical Damage']
    df['edps'] = (df['Cold Damage'] + df['Fire Damage'] + df['Lightning Damage']) * df['Attacks per Second']
    df = df.drop(columns=[
        'Attacks per Second',
        'Physical Damage',
        'Cold Damage',
        'Fire Damage',
        'Lightning Damage'
    ])
    df = df.drop(columns=local_weapon_mods)
    df = df.select_dtypes(include=['int64', 'float64'])
    df = df.drop(columns=['rarity', 'minutes_since_listed', 'minutes_since_league_start', 'open_prefixes', 'open_suffixes'])
    df.fillna(0, inplace=True)

    plt.figure(figsize=(10, 8))
    corr_matrix = df.corr()
    sns.heatmap(corr_matrix[['exalts']].sort_values(by='exalts', ascending=False), annot=True, cmap='coolwarm')
    plt.show()

    features = df.drop(columns=['exalts'])

    target_col = df['exalts']

    features.fillna(0, inplace=True)

    f_train, f_test, t_train, t_test = train_test_split(features, target_col, test_size=0.2, random_state=42)

    print(f"X_train shape: {f_train.shape}")
    print(f"y_train shape: {t_train.shape}")

    train_data = xgb.DMatrix(f_train, label=t_train)
    test_data = xgb.DMatrix(f_test, label=t_test)

    logging.info("Prepped data.")

    depths = [8, 12, 16]
    etas = [0.01, 0.05, 0.1]
    num_boost_rounds = [5000, 10000, 25000]

    train_combos = list(itertools.product(depths, etas, num_boost_rounds))
    random.shuffle(train_combos)
    for depth, eta, num_boost_round in train_combos:
        logging.info(f"Depth: {depth}, ETA: {eta}, Boost rounds: {num_boost_round}")
        params = {
            'max_depth': depth,  # Maximum depth of a tree
            'eta': eta,  # Learning rate
            'eval_metric': 'rmse'  # Root Mean Square Error,
        }

        evals = [(train_data, 'train'), (test_data, 'test')]

        model = xgb.train(params,
                          train_data,
                          num_boost_round=num_boost_round,
                          early_stopping_rounds=50,
                          evals=evals,
                          obj=custom_objective,
                          verbose_eval=False)

        t_predict = model.predict(test_data)

        mse = utils.weighted_mse(t_test, t_predict)
        logging.info(f"Weighted Mean Squared Error: {mse}")

        training_df = pd.concat([t_test, f_test], axis=1)
        training_df['Predicted Price'] = t_predict

        # Add a column for the absolute error
        training_df['Absolute Error'] = (training_df['Predicted Price'] - training_df['exalts']).abs()

        # Sort the dataframe by the absolute error in descending order
        outliers_df = training_df.sort_values(by='Absolute Error', ascending=False)

        # Show only the rows where we the actual price (exalts) was less than the predicted price
        outliers_df = outliers_df[outliers_df['exalts'] - outliers_df['Predicted Price'] < 0]

        # Get feature importances
        importance = model.get_score(importance_type='weight')

        # Create a DataFrame for easier plotting
        importance_df = pd.DataFrame(list(importance.items()), columns=['Feature', 'Importance'])
        importance_df = importance_df.sort_values(by='Importance', ascending=False)

        # Plot the feature importances
        importance_df.plot(kind='barh', x='Feature', y='Importance', legend=False, figsize=(10, 6))
        plt.title('Feature Importance')
        plt.xlabel('Importance')
        plt.ylabel('Feature')
        plt.show()

        plt.figure(figsize=(8, 5))
        plt.scatter(t_predict, t_test, alpha=0.5)
        plt.plot([0, 4000], [0, 4000], color='red', linestyle='--')
        plt.xlabel("Predicted Price (Exalts)")
        plt.ylabel("Actual Prices (Exalts)")

        plt.title("Actual vs. Predicted Prices")
        plt.grid(True)
        plt.show()

        df['exalts'].hist()
        plt.show()
