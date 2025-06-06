import itertools

import numpy as np
import pandas as pd
from sklearn.neighbors import RadiusNeighborsRegressor
from sklearn.preprocessing import StandardScaler

from program_logging import LogFile, LogsHandler
from . import utils

stats_log = LogsHandler().fetch_log(LogFile.STATS_PREP)


class CorrelationAnalyzer:

    @staticmethod
    def determine_single_column_weights(features,
                                        prices,
                                        correlation_threshold: float,
                                        weight_multiplier: float = None) -> dict:
        corrs = features.corrwith(prices)
        mod_weights = dict()
        for mod, corr in corrs.items():
            if corr >= correlation_threshold:
                mod_weights[mod] = corr

        if weight_multiplier:
            mod_weights = {mod: weight * weight_multiplier for mod, weight in mod_weights.items()}

        return mod_weights

    @staticmethod
    def determine_column_pair_weights(features: pd.DataFrame,
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
                stats_log.info(f"Valid column correlation {(mod1, mod2)}: {corr_val}")
                valid_pairs_weights[(mod1, mod2)] = corr_val

        return valid_pairs_weights


class DataFramePrep:

    def __init__(self,
                 dataframe: pd.DataFrame,
                 price_col_name: str):
        self._df = dataframe

        self.price_col_name = price_col_name
        self.log_col_name = None

    def __getattr__(self, attr):
        # Delegate all missing attributes to the internal DataFrame
        return getattr(self._df, attr)

    def __getitem__(self, key):
        return self._df[key]

    def __setitem__(self, key, value):
        self._df[key] = value

    def __repr__(self):
        return repr(self._df)

    @property
    def df(self):
        return self._df

    def log_price(self,
                  price_col_name: str,
                  log_col_name: str):
        self.df[log_col_name] = np.log1p(self.df[price_col_name])
        self.log_col_name = log_col_name
        return self

    def fetch_price_column(self):
        return self.df[self.price_col_name]

    def fetch_log_price_column(self):
        return self.df[self.log_col_name]

    def fetch_features(self) -> pd.DataFrame:
        target_cols = [col for col in [self.price_col_name, self.log_col_name] if col is not None]
        feature_cols = [col for col in self._df.columns if col not in target_cols]

        return self._df[feature_cols]

    def drop_nan_rows(self):
        features_df = self.fetch_features()

        valid_indices = features_df[~((features_df == 0) | (pd.isna(features_df))).all(axis=1)].index

        self._df = self._df.loc[valid_indices]

    def drop_overly_null_columns(self, max_percent_nulls: float):
        null_counts = dict()
        for col in self._df.columns:
            zero_rows = self._df[col] == 0
            na_rows = pd.isna(self._df[col])
            null_rows = zero_rows | na_rows

            null_counts[col] = null_rows.sum()

        valid_cols = [col for col, nulls_count in null_counts.items()
                      if nulls_count / len(self._df) < max_percent_nulls]
        self._df = self._df[valid_cols]

        return self

    def drop_overly_modal_columns(self, max_percent_mode: float):
        mode_counts = dict()
        for col in self._df.columns:
            mode_value = self._df[col].mode()[0]
            mode_counts[col] = (self._df[col] == mode_value).sum()

        valid_cols = [col for col, mode_count in mode_counts.items()
                      if mode_count / len(self._df) < max_percent_mode]
        self._df = self._df[valid_cols]

        return self

    def create_paired_columns(self, column_pairs: list):
        paired_cols = dict()
        for mod1, mod2 in column_pairs:
            paired_cols[f"{mod1}_{mod2}"] = self._df[mod1] * self._df[mod2]

        for col_name, col in paired_cols.items():
            self._df[col_name] = col

        return self

    def normalize_features(self):
        features_df = self.fetch_features()
        original_cols = features_df.columns

        scaler = StandardScaler()
        new_data = scaler.fit_transform(features_df)
        new_df = pd.DataFrame(new_data)
        new_df.columns = original_cols

        self._df = new_df

        return self

    def apply_column_weights(self, weights: dict):
        for col, weight in weights.items():
            self._df[col] = self._df[col] * weight

        return self

    def remove_indices(self, indices):
        self._df = self._df.iloc[indices]

        return self


class StatsPrep:

    def __init__(self, plot_visuals):
        self._plot_visuals = plot_visuals

    @staticmethod
    def _apply_determine_market_price(row):
        """
        Not currently in use
        """
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

        """
        cum_weight = 0
        for current_weight, current_price in zip(sorted_weights, sorted_prices):
            cum_weight += current_weight

            if cum_weight >= weighted_bottom and listed_price < current_price:
                print(f"Listed price: {listed_price}\nReturned price: {current_price}"
                      f"\nSorted prices: {str(sorted_prices)}\nSorted weights: {str(sorted_weights)}")
                return current_price

            # If we hit the top of the weight range, then check the listed price against the
            # top of the price range (which is the loop's current price)
            if cum_weight >= weighted_top:
                if listed_price > current_price:
                    print(f"Listed price: {listed_price}\nReturned price: {current_price}"
                          f"\nSorted prices: {str(sorted_prices)}\nSorted weights: {str(sorted_weights)}")
                    return current_price
                else:  # This condition indicates that the listed price was within the bottom and top weight range
                    print(f"Listed price: {listed_price}\nReturned price: {listed_price}"
                          f"\nSorted prices: {str(sorted_prices)}\nSorted weights: {str(sorted_weights)}")
                    return listed_price
        """

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
        radius_neighbors = RadiusNeighborsRegressor(radius=radius_range)
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

    def prep_dataframe(self, df: pd.DataFrame, price_column: str):
        df_prep = (
            DataFramePrep(df, price_col_name='divs')
            .fillna(0)
            .select_dtypes(['int64', 'float64'])
            .log_price(log_column_name='log_divs')
            .drop_nan_rows()
            .reset_index(drop=True)
            .drop_overly_null_columns(max_percent_nulls=0.97)
            .drop_overly_modal_columns(max_percent_mode=0.97)
        )
        features_df = df_prep.fetch_features()

        single_column_weights = CorrelationAnalyzer.determine_single_column_weights(
            features=features_df,
            prices=df_prep.fetch_log_price_columns,
            correlation_threshold=0.4,
            weight_multiplier=2.5
        )

        column_pair_weights = CorrelationAnalyzer.determine_column_pair_weights(
            features=features_df,
            prices=df_prep.fetch_log_price_columns,
            correlation_threshold=0.4
        )

        if not single_column_weights and not column_pair_weights:
            return

        column_pairs = list(column_pair_weights.keys())
        single_columns = list(single_column_weights.keys())

        if column_pairs:
            df_prep.create_paired_columns(column_pairs)

        (df_prep
         .normalize_features()
         .apply_column_weights(weights={**single_column_weights, **column_pair_weights})
         )

        """igs = dict(zip(norm_features.columns, mutual_info_regression(norm_features, prices)))
        igs = {col: ig for col, ig in igs.items() if ig >= 0.10}
        norm_features = norm_features[list(igs.keys())]"""

        """plot = pd.concat([tr_features, log_prices])

        plt.figure(figsize=(10, 7))
        plt.title("Before nearest neighbor")
        sns.scatterplot(x=plot['max_quality_pdps'],
                        y=plot[f"log_{price_column}"])
        plt.show()"""

        stats_log.info("Determining correct prices and isolated indices via NearestNeighbor.")
        # We pass in prices instead of log_prices here on purpose to KNN
        new_prices, out_of_range_indices = self._normalize_prices_via_nearest_neighbor(
            features_df=df_prep.fetch_features(),
            prices=df_prep.fetch_log_price_column
        )

        df_prep.remove_indices(out_of_range_indices)

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
