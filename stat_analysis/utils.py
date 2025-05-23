import pandas as pd


def normalize_column_name(col: str | tuple) -> str:
    return f"{col[0]}_{col[1]}" if isinstance(col, tuple) else col


def _determine_number_of_infrequent_values(df, col):
    most_frequent_value = df[col].mode()[0]
    non_constant_count = df[df[col] != most_frequent_value].count()


def filter_insignificant_columns(df, variance_threshold: float) -> pd.DataFrame:
    non_blank_cols = df.columns[(df > 0).any() & (~df.isna()).any()]
    df = df[non_blank_cols]

    # Filter out columns that have less than 30 values that are not the mode value
    invalid_cols = []
    for col in df.columns:
        most_frequent_value = df[col].mode()[0]

        non_constant_count = df[df[col] != most_frequent_value].count()
        if non_constant_count < 30:
            invalid_cols.append(col)
            continue

        variance = non_constant_count / len(df)
        if variance >= variance_threshold: # If there's enough non-mode values then this column is okay
            continue

        variance_df = df[df[col] != most_frequent_value]
        corr_val = variance_df

    df = df.drop(columns=invalid_cols)



    return df

def filter_out_blank_columns(df):
    non_negative_rows = (df > 0).all(axis=1)
    no_nans = ~df.isna().any(axis=1)

    filtered_df = df[non_negative_rows & no_nans]

    return filtered_df


class DataFrameModifier:

    def __init__(self, df: pd.DataFrame, price_col: str):
        self._original_df = df.copy()
        
        self.prices = df[price_col]
        self._df = df.drop(columns=[price_col])

    def normalize_col_names(self, cols: list[tuple | str]):
        col_renames = {
            col: f"{col[0]}_{col[1]}" if isinstance(col, tuple) else col
            for col in cols
        }
        self._df = self._df.rename(col_renames)

        return self

    def get_nonzero_rows(self, cols: list[str]):
        return self._df[(self._df[cols] != 0).all(axis=1)]

    def get(self, reset_df: bool = True) -> pd.DataFrame:
        if not reset_df:
            return self._df

        return_df = self._df.copy()
        self._df = self._original_df
        return return_df
    
    