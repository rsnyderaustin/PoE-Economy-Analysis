import json
import logging
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
import xgboost as xgb

import seaborn as sns
import pandas as pd

from shared import PathProcessor


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
        '#% increased Attack Speed'
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
    df = df.drop(columns=['minutes_since_listed', 'minutes_since_league_start', 'open_prefixes', 'open_suffixes'])
    df.fillna(0, inplace=True)
    # df = df.drop(columns=['currency_amount'])

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

    params = {
        'objective': 'reg:squarederror',  # Use 'reg:squarederror' for regression
        'max_depth': 8,  # Maximum depth of a tree
        'eta': 0.01,  # Learning rate
        'eval_metric': 'rmse'  # Root Mean Square Error
    }

    evals = [(train_data, 'train'), (test_data, 'test')]

    logging.info("Beginning model training.")
    model = xgb.train(params,
                      train_data,
                      num_boost_round=10000,
                      early_stopping_rounds=50,
                      evals=evals,
                      verbose_eval=True)
    logging.info("Finished model training.")

    t_predict = model.predict(test_data)
    mse = mean_squared_error(t_test, t_predict)
    logging.info(f"Mean Squared Error: {mse}")

    training_df = pd.concat([t_test, f_test], axis=1)
    training_df['Predicted Price'] = t_predict

    # Add a column for the absolute error
    training_df['Absolute Error'] = (training_df['Predicted Price'] - training_df['exalts']).abs()

    # Sort the dataframe by the absolute error in descending order
    outliers_df = training_df.sort_values(by='Absolute Error', ascending=False)

    # Display the top 10 largest outliers
    print(outliers_df.head(10))

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
