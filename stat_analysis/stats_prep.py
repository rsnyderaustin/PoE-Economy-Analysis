import itertools
import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.neighbors import RadiusNeighborsClassifier
from sklearn.preprocessing import StandardScaler

from . import utils


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
    def determine_pair_column_weights(features: pd.DataFrame,
                                      prices,
                                      correlation_threshold: float) -> dict:
        mod_combinations = list(itertools.combinations(features.columns, 2))

        # Step 1: Build initial dictionary of DataFrames filtered by nonzero indices
        filtered_dfs = {
            (mod1, mod2): utils.filter_out_empty_rows(features[[mod1, mod2]])
            for mod1, mod2 in mod_combinations
        }

        # Step 2: Filter out DataFrames with fewer than 30 samples
        pair_dfs = {pair: pair_df for pair, pair_df in filtered_dfs.items() if len(pair_df) >= 30}

        # Step 3: Determine how each mod pair correlates with the price of the item
        valid_pairs_weights = dict()
        for (mod1, mod2), pair_df in pair_dfs.items():
            # Create a dataframe with a single column that is the product of mod columns
            product_df = pd.DataFrame({(mod1, mod2): pair_df[mod1] * pair_df[mod2]})

            # In rare cases, multiplying two columns together creates a column of all the same value
            mode_val = product_df[(mod1, mod2)].mode()[0]
            mode_count = (product_df[(mod1, mod2)] == mode_val).sum()
            if mode_count == len(product_df):
                continue

            pair_corr = product_df.corrwith(prices)
            corr_val = pair_corr[(mod1, mod2)]
            if corr_val >= correlation_threshold:
                logging.info(f"Valid column correlation {(mod1, mod2)}: {corr_val}")
                valid_pairs_weights[(mod1, mod2)] = corr_val

        return valid_pairs_weights


class StatsPrep:

    @classmethod
    def _determine_insignificant_columns(cls,
                                         features_df: pd.DataFrame,
                                         non_null_count_threshold: int = 50,
                                         non_mode_count_threshold: int = 50,
                                         non_mode_percent_threshold: float = 0.02,
                                         non_null_percent_threshold: float = 0.02) -> set[str]:
        invalid_cols = set()
        empty_cols = features_df.columns[((features_df == 0) | (pd.isna(features_df))).all()]
        invalid_cols.update(empty_cols)

        null_counts = cls._determine_null_counts(features_df)
        mode_counts = cls._determine_mode_counts(features_df)

        total_count = len(features_df)
        for col in features_df.columns:
            non_nulls = total_count - null_counts[col]
            non_nulls_percent = non_nulls / total_count

            if non_nulls < non_null_count_threshold:
                invalid_cols.add(col)
                continue

            if non_nulls_percent < non_null_percent_threshold:
                invalid_cols.add(col)
                continue

            non_modes = total_count - mode_counts[col]
            non_modes_percent = non_modes / total_count

            if non_modes < non_mode_count_threshold:
                invalid_cols.add(col)
                continue

            if non_modes_percent < non_mode_percent_threshold:
                invalid_cols.add(col)
                continue

        return invalid_cols

    @staticmethod
    def _apply_determine_market_price(row):
        listed_price = row['real_price']
        distances = pd.Series(row['distances'])
        weights = (1 / (distances + 0.1))

        prices = pd.Series(row['prices'])
        sorted_indices = np.argsort(prices)

        sorted_prices = prices[sorted_indices]
        sorted_weights = weights[sorted_indices]

        total_weight = sum(sorted_weights)
        weighted_bottom = total_weight * 0.1
        weighted_top = total_weight * 0.35

        cum_weight = 0
        for current_weight, current_price in zip(sorted_weights, sorted_prices):
            cum_weight += current_weight

            if cum_weight >= weighted_bottom and listed_price < current_price:
                """print(f"Listed price: {listed_price}\nReturned price: {current_price}"
                      f"\nSorted prices: {str(sorted_prices)}\nSorted weights: {str(sorted_weights)}")"""
                return current_price

            # If we hit the top of the weight range, then check the listed price against the
            # top of the price range (which is the loop's current price)
            if cum_weight >= weighted_top:
                if listed_price > current_price:
                    """print(f"Listed price: {listed_price}\nReturned price: {current_price}"
                          f"\nSorted prices: {str(sorted_prices)}\nSorted weights: {str(sorted_weights)}")"""
                    return current_price
                else:  # This condition indicates that the listed price was within the bottom and top weight range
                    """print(f"Listed price: {listed_price}\nReturned price: {listed_price}"
                          f"\nSorted prices: {str(sorted_prices)}\nSorted weights: {str(sorted_weights)}")"""
                    return listed_price

    @staticmethod
    def _apply_visualize_neighbors(row, features_df: pd.DataFrame, return_data: dict):
        print(f"Current idx: {row.name}")
        
        distances = pd.Series(row['neighbor_distances'])
        weights = (1 / (distances + 0.1))

        prices = pd.Series(row['neighbor_prices'])
        sorted_indices = np.argsort(prices)

        sorted_prices = prices[sorted_indices]
        sorted_weights = weights[sorted_indices]

        for idx in sorted_indices:
            item_features = features_df.iloc[row.name].to_dict()
            for col, val in item_features.items():
                if col not in return_data:
                    return_data[col] = list()
                return_data[col].append(val)

            listed_price = row['item_price']
            if 'item_price' not in return_data:
                return_data['item_price'] = list()
            return_data['item_price'].append(listed_price)

            neighbor_features = features_df.iloc[idx].to_dict()
            for col, val in neighbor_features.items():
                if f"neighbor_{col}" not in return_data:
                    return_data[f"neighbor_{col}"] = list()
                
                return_data[f"neighbor_{col}"].append(val)
                
            if "neighbor_price" not in return_data:
                return_data[f"neighbor_price"] = []
            neighbor_price = sorted_prices.iloc[idx]
            return_data[f"neighbor_price"].append(neighbor_price)
            
            if "neighbor_weight" not in return_data:
                return_data[f"neighbor_weight"] = []
            neighbor_weight = sorted_weights.iloc[idx]
            return_data[f"neighbor_weight"].append(neighbor_weight)

    @classmethod
    def _normalize_prices_via_nearest_neighbor(cls,
                                               features_df: pd.DataFrame,
                                               prices: pd.Series,
                                               min_neighbors: int = 20,
                                               radius_range: float = 0.5) -> tuple[pd.Series, list]:
        features_df = features_df.reset_index(drop=True)
        radius_neighbors = RadiusNeighborsClassifier(radius=radius_range, weights='distance')
        radius_neighbors.fit(features_df, prices)
        distances, indices = radius_neighbors.radius_neighbors(features_df)

        isolated_indices = [i for i, distances in enumerate(distances) if len(distances) < min_neighbors]

        """vis_df = pd.DataFrame({
            'neighbor_distances': distances.tolist(),
            'neighbor_indices': indices.tolist(),
            'neighbor_prices': [prices.iloc[idx].tolist() for idx in indices],
            'item_price': prices
        })

        vis_data = dict()
        vis_df.apply(cls._apply_visualize_neighbors, args=(features_df, vis_data), axis=1)
        vis_df = pd.DataFrame(vis_data)
        vis_df = vis_df[~vis_df.index.isin(isolated_indices)]"""

        cols_dict = {
            'distances': distances.tolist(),
            'prices': [prices.iloc[idx].tolist() for idx in indices]
        }
        df = pd.DataFrame(cols_dict)

        df['real_price'] = prices

        prices = df.apply(cls._apply_determine_market_price, axis=1)
        return prices, isolated_indices

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
    def _pair_columns(features_df: pd.DataFrame,
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

    @classmethod
    def _determine_mode_counts(cls, df: pd.DataFrame) -> dict:
        mode_counts = dict()
        for col in df.columns:
            mode_value = df[col].mode()[0]
            mode_counts[col] = (df[col] == mode_value).sum()

        return mode_counts

    @staticmethod
    def _determine_null_counts(df: pd.DataFrame) -> dict:
        null_counts = dict()
        for col in df.columns:
            zero_rows = df[col] == 0
            na_rows = pd.isna(df[col])
            null_rows = zero_rows | na_rows
            null_counts[col] = null_rows.sum()

        return null_counts

    @staticmethod
    def _prep_dataframe(df: pd.DataFrame, price_column: str) -> tuple:
        df = df.reset_index(drop=True)
        df = df.select_dtypes(['int64', 'float64'])
        df = df.fillna(0)

        df[f"log_{price_column}"] = np.log1p(df[price_column])

        features_df = df.drop(columns=[price_column, f"log_{price_column}"])
        prices = df[price_column]
        log_prices = df[f"log_{price_column}"]

        # Drop all rows where all values are either 0 or NaN
        features_df = features_df[~((features_df == 0) | (pd.isna(features_df))).all(axis=1)]

        return features_df, prices, log_prices

    @classmethod
    def prep_dataframe(cls, df: pd.DataFrame, price_column: str):
        features_df, prices, log_prices = cls._prep_dataframe(df,
                                                              price_column=price_column)

        insignificant_cols = cls._determine_insignificant_columns(features_df=features_df)
        features_df = features_df.drop(columns=list(insignificant_cols))

        single_column_weights = CorrelationAnalyzer.determine_single_column_weights(
            features=features_df,
            prices=log_prices,
            correlation_threshold=0.4
        )
        single_column_weights = {col: weight * 2.5 for col, weight in single_column_weights.items()}

        pair_column_weights = CorrelationAnalyzer.determine_pair_column_weights(
            features=features_df,
            prices=log_prices,
            correlation_threshold=0.4
        )
        if not single_column_weights and not pair_column_weights:
            return

        valid_columns = list(single_column_weights.keys()) + list(pair_column_weights.keys())

        logging.info("Combining column pairs into their product.")
        tr_features = cls._pair_columns(features_df=features_df.copy(),
                                        columns=valid_columns)

        logging.info("Normalizing data.")
        norm_features = cls._normalize_data(features_df=tr_features.copy())

        """igs = dict(zip(norm_features.columns, mutual_info_regression(norm_features, prices)))
        igs = {col: ig for col, ig in igs.items() if ig >= 0.10}
        norm_features = norm_features[list(igs.keys())]"""

        logging.info("Weighting data.")
        single_column_weights = {utils.normalize_column_name(col): weight for col, weight in single_column_weights.items()}
        pair_column_weights = {utils.normalize_column_name(col): weight for col, weight in pair_column_weights.items()}
        norm_features = cls._weight_data(features_df=norm_features,
                                         column_weights={**single_column_weights, **pair_column_weights})

        """plot = pd.concat([tr_features, log_prices])

        plt.figure(figsize=(10, 7))
        plt.title("Before nearest neighbor")
        sns.scatterplot(x=plot['max_quality_pdps'],
                        y=plot[f"log_{price_column}"])
        plt.show()"""

        logging.info("Determining correct prices and isolated indices via NearestNeighbor.")
        # We pass in prices instead of log_prices here on purpose to KNN
        new_prices, out_of_range_indices = cls._normalize_prices_via_nearest_neighbor(
            features_df=norm_features.copy(),
            prices=prices.copy()
        )

        tr_features = tr_features[~tr_features.index.isin(out_of_range_indices)]
        df = tr_features

        df[price_column] = new_prices
        df[f"log_{price_column}"] = np.log1p(new_prices)

        # visualize.plot_pca(df, price_column=f"log_{price_column}")
        # visualize.plot_dimensions(df, price_column=price_column, atype=atype)

        """plt.figure(figsize=(10, 7))
        plt.title("After nearest neighbor")
        sns.scatterplot(x=df['max_quality_pdps'],
                        y=df[f"log_{price_column}"])
        plt.show()"""

        return df
