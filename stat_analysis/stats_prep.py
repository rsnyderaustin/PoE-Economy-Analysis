import logging
import itertools

from dataclasses import dataclass
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestRegressor
from sklearn.neighbors import RadiusNeighborsRegressor, KNeighborsRegressor
from sklearn.preprocessing import StandardScaler

from . import utils, visualize


class DataFrameParts:

    def __init__(self, df: pd.DataFrame, price_column: str):
        self.df = df
        self.prices = df[price_column]
        self.features = df.drop(columns=[price_column]).select_dtypes(['int64', 'float64']).fillna(0)


@dataclass
class CorrelationResults:
    transformed_features: pd.DataFrame
    single_weights: dict
    pair_weights: dict


class CorrelationAnalyzer:

    @staticmethod
    def determine_single_column_weights(features, prices, correlation_threshold: float) -> dict:
        corrs = features.corrwith(prices)
        mod_weights = dict()
        for mod, corr in corrs.items():
            if corr >= correlation_threshold:
                mod_weights[mod] = corr

        return mod_weights

    @staticmethod
    def determine_pair_column_weights(features: pd.DataFrame, prices, correlation_threshold: float) -> dict:
        mod_combinations = list(itertools.combinations(features.columns, 2))

        # Step 1: Build initial dictionary of DataFrames filtered by nonzero indices
        filtered_dfs = {
            (mod1, mod2): utils.get_nonzero_dataframe(features, [mod1, mod2])
            for mod1, mod2 in mod_combinations
        }

        # Step 2: Filter out DataFrames with fewer than 30 samples
        pair_dfs = {pair: pair_df for pair, pair_df in filtered_dfs.items() if len(pair_df) >= 30}

        # Step 3: Determine how each mod pair correlates with the price of the item
        valid_pairs_weights = dict()
        for (mod1, mod2), pair_df in pair_dfs.items():
            # Create a dataframe with a single column that is the product of mod columns
            product_df = pd.DataFrame({(mod1, mod2): pair_df[mod1] * pair_df[mod2]})

            pair_corr = product_df.corrwith(prices)
            corr_val = pair_corr[(mod1, mod2)]
            if corr_val >= correlation_threshold:
                logging.info(f"{(mod1, mod2)} correlation: {corr_val}")
                valid_pairs_weights[(mod1, mod2)] = corr_val

        return valid_pairs_weights


class StatsPrep:

    @classmethod
    def _determine_insignificant_columns(cls,
                                         features_df: pd.DataFrame,
                                         prices: pd.Series,
                                         non_null_count_threshold: int = 50,
                                         non_mode_count_threshold: int = 50,
                                         non_mode_percent_threshold: float = 0.05,
                                         non_null_percent_threshold: float = 0.05,
                                         correlation_threshold: float = 0.5) -> set[str]:
        invalid_cols = set()
        empty_cols = features_df.columns[((features_df == 0) | (pd.isna(features_df))).all()]
        invalid_cols.update(empty_cols)

        non_null_counts = cls._determine_non_null_value_counts(features_df)
        non_mode_counts = cls._determine_non_mode_value_counts(features_df)

        invalid_cols.update([col for col, non_nulls in non_null_counts.items()
                             if non_nulls < non_null_count_threshold])
        invalid_cols.update([col for col, non_mode in non_mode_counts.items()
                             if non_mode < non_mode_count_threshold])

        valid_cols = [col for col in features_df.columns if col not in invalid_cols]

        for col in valid_cols:
            percent_null = non_null_counts[col] / len(features_df)
            if percent_null < non_null_percent_threshold:
                non_null_df = features_df[(features_df[col] != 0) & ~pd.isna(features_df[col])]
                non_null_series = non_null_df[col]

                corr_val = non_null_series.corr(prices)
                if pd.isna(corr_val) or corr_val < correlation_threshold:  # Is NA when all non-null values are the same
                    invalid_cols.add(col)
                    continue

            percent_non_mode = non_mode_counts[col] / len(features_df)
            if percent_non_mode < non_mode_percent_threshold:
                mode_value = features_df[col].mode()[0]

                variance_df = features_df[features_df[col] != mode_value]
                variance_series = variance_df[col]

                corr_val = variance_series.corr(prices)
                if pd.isna(corr_val) or corr_val < correlation_threshold: # Is NA when all non-mode values are the same
                    invalid_cols.add(col)
                    continue

        return invalid_cols

    @staticmethod
    def _apply_predict_price(row):
        distances = pd.Series(row['distances'])
        weights = (1 / (distances + 0.1))

        prices = pd.Series(row['prices'])
        sorted_indices = np.argsort(prices)

        sorted_prices = prices[sorted_indices]
        sorted_weights = weights[sorted_indices]

        weighted_median_20 = np.sum(sorted_weights) * 0.2

        current_weight = 0
        for weight, price in zip(sorted_weights, sorted_prices):
            current_weight += weight
            if current_weight >= weighted_median_20:
                return price

    @classmethod
    def _determine_nearest_neighbor_outliers(cls,
                                             features_df: pd.DataFrame,
                                             prices: pd.Series,
                                             radius: float = 0.5,
                                             price_deviation_threshold=0.15) -> set[int]:
        regressor = KNeighborsRegressor(n_neighbors=18, weights='distance')
        regressor.fit(features_df, prices)
        distances, indices = regressor.kneighbors(features_df)

        outlier_indices = set()
        out_of_range_indices = {
            i for i, array in enumerate(distances)
            if not all(distance <= radius for distance in array)
        }
        outlier_indices.update(out_of_range_indices)

        cols_dict = {
            'distances': distances.tolist(),
            'prices': [prices.iloc[idx].tolist() for idx in indices]
        }
        df = pd.DataFrame(cols_dict)

        df['predicted_price'] = df.apply(cls._apply_predict_price, axis=1)

        df['real_price'] = prices

        df['price_deviation'] = df['real_price'] - df['predicted_price']

        df['is_outlier'] = df['price_deviation'].abs() > price_deviation_threshold

        outlier_indices.update(list(df[df['is_outlier']].index))
        return outlier_indices

    @staticmethod
    def _normalize_data(features_df: pd.DataFrame) -> pd.DataFrame:
        original_cols = features_df.columns

        features_df.columns = [utils.normalize_column_name(col) for col in features_df.columns]
        scaler = StandardScaler()
        new_data = scaler.fit_transform(features_df)
        new_df = pd.DataFrame(new_data)
        new_df.columns = original_cols
        return new_df

    @staticmethod
    def _transform_columns(features_df: pd.DataFrame,
                           columns: list[str | tuple]) -> pd.DataFrame:
        df_setup = dict()

        single_columns = [col for col in columns if isinstance(col, str)]
        df_setup.update({col: features_df[col] for col in single_columns})

        pair_columns = [col for col in columns if isinstance(col, tuple)]
        for mod1, mod2 in pair_columns:
            df_setup[utils.normalize_column_name((mod1, mod2))] = features_df[mod1] * features_df[mod2]

        return pd.DataFrame(df_setup)

    @staticmethod
    def _weight_data(features_df: pd.DataFrame,
                     column_weights: dict) -> pd.DataFrame:
        new_cols = {}
        for col, weight in column_weights.items():
            new_cols[col] = features_df[col] * weight

        return pd.DataFrame(new_cols)

    @staticmethod
    def _count_not_mode(df_column):
        mode_value = df_column.mode()[0]
        return (df_column != mode_value).sum()

    @classmethod
    def _determine_non_mode_value_counts(cls, df: pd.DataFrame) -> dict:
        not_mode_counts = {col: cls._count_not_mode(df[col]) for col in df.columns}

        return not_mode_counts

    @staticmethod
    def _determine_non_null_value_counts(df: pd.DataFrame) -> dict:
        non_zero_non_nan_counts = {col: ((df[col] != 0) & ~pd.isna(df[col])).sum() for col in df.columns}

        return non_zero_non_nan_counts

    @classmethod
    def prep_data(cls, df: pd.DataFrame, price_column: str, atype: str):
        df = df.reset_index(drop=True)
        df = df.select_dtypes(['int64', 'float64'])
        df = df.fillna(0)

        print(df.duplicated().sum())

        df[price_column] = np.log1p(df[price_column])

        features = df.drop(columns=[price_column])
        prices = df[price_column]

        # Drop all rows where all values are either 0 or NaN
        features = features[~((features == 0) | (pd.isna(features))).all(axis=1)]

        insignificant_cols = cls._determine_insignificant_columns(
            features_df=features,
            prices=prices
        )
        features = features.drop(columns=insignificant_cols)

        single_column_weights = CorrelationAnalyzer.determine_single_column_weights(
            features=features,
            prices=prices,
            correlation_threshold=0.4
        )
        pair_column_weights = CorrelationAnalyzer.determine_pair_column_weights(
            features=features,
            prices=prices,
            correlation_threshold=0.4
        )
        if not single_column_weights and not pair_column_weights:
            return

        valid_columns = list(single_column_weights.keys()) + list(pair_column_weights.keys())
        tr_features = cls._transform_columns(features_df=features.copy(),
                                             columns=valid_columns)

        non_normalized_features = tr_features.copy()

        non_normalized_features['exalts'] = prices

        """ Normalize column / column pair correlations """
        single_column_weights = {utils.normalize_column_name(col): val for col, val in single_column_weights.items()}
        pair_column_weights = {utils.normalize_column_name(col): val for col, val in pair_column_weights.items()}

        tr_features = cls._normalize_data(features_df=tr_features.copy())
        tr_features = cls._weight_data(features_df=tr_features.copy(),
                                       column_weights={**single_column_weights, **pair_column_weights})

        plot = pd.concat([tr_features, prices])

        plt.figure(figsize=(10, 7))
        plt.title("Before removing outliers")
        sns.scatterplot(x=plot['max_quality_pdps'],
                        y=plot['exalts'])
        plt.show()

        outlier_indices = cls._determine_nearest_neighbor_outliers(
            features_df=tr_features.copy(),
            prices=prices.copy()
        )

        non_normalized_features = non_normalized_features[~non_normalized_features.index.isin(outlier_indices)]
        df = non_normalized_features

        plt.figure(figsize=(10, 7))
        plt.title("After filtering outliers.")
        df['exalts'] = prices
        sns.scatterplot(x=df['max_quality_pdps'],
                        y=df['exalts'])
        plt.show()

        # visualize.plot_dimensions(df=df, atype=atype)

        return df

