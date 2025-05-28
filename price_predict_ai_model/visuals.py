import pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns


def _apply_log_outliers(row):
    non_null_dict = {col: val for col, val in row.items()
                     if pd.notna(val) and val > 0.0 and col not in ['Predicted Price', 'divs']}

    print(f"\n\n")
    print(f"Predicted Price: {row['Predicted Price']}"
          f"\nActual Price: {row['divs']}"
          f"\n\tAttributes and values:")

    for k, v in non_null_dict.items():
        print(f"\t{k}: {v}")


def log_outliers(outliers_df):
    outliers_df.apply(_apply_log_outliers, axis=1)


def plot_correlation_matrix(df: pd.DataFrame):
    corr_df = df.select_dtypes(include=['int64', 'float64'])
    plt.figure(figsize=(18, 8))
    corr_matrix = corr_df.corr()
    sns.heatmap(corr_matrix[['divs']].sort_values(by='divs', ascending=False), annot=True, cmap='coolwarm')
    plt.show()


def plot_feature_importance(model, atype: str):
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


def plot_actual_vs_predicted(atype, test_predictions, test_targets):
    min_predict_axis = min(test_predictions) * 0.8
    max_predict_axis = max(test_predictions) * 1.2

    min_target_axis = min(test_targets) * 0.8
    max_target_axis = max(test_targets) * 1.2

    plt.figure(figsize=(8, 5))
    plt.scatter(test_predictions, test_targets, alpha=0.5)
    plt.plot([min_predict_axis, max_predict_axis], [min_target_axis, max_target_axis], color='red', linestyle='--')
    plt.xlabel("Predicted Price (Divs)")
    plt.ylabel("Actual Prices (Divs)")

    plt.title(f"Actual vs. Predicted Prices for {atype}")
    plt.grid(True)
    plt.show()


def print_outliers(test_target_df: pd.DataFrame,
                   test_features_df: pd.DataFrame,
                   test_predictions):
    training_df = pd.concat([test_target_df, test_features_df], axis=1)
    training_df['Predicted Price'] = test_predictions

    # Add a column for the absolute error
    training_df['Absolute Error'] = (training_df['Predicted Price'] - training_df['divs']).abs()

    under_priced_df = training_df[training_df['divs'] - training_df['Predicted Price'] < 0]

    # Sort the dataframe by the absolute error in descending order
    outliers_df = under_priced_df.sort_values(by='Absolute Error', ascending=False).head(3)
    log_outliers(outliers_df)
