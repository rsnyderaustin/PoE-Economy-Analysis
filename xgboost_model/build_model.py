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
    df = df.select_dtypes(include=['int64', 'float64'])

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

    plt.figure(figsize=(8, 5))
    plt.scatter(t_test, t_predict, alpha=0.5)
    plt.plot([0, 4000], [0, 4000], color='red', linestyle='--')
    plt.xlabel("Actual Prices (Exalts)")
    plt.ylabel("Predicted Prices (Exalts)")
    plt.title("Actual vs. Predicted Prices")
    plt.grid(True)
    plt.show()

    df['exalts'].hist()
    plt.show()
