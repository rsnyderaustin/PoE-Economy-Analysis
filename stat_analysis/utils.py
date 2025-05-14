import pandas as pd


def filter_blank_columns(df) -> pd.DataFrame:
    non_blank_cols = df.columns[(df > 0).any() & (~df.isna()).any()]
    df = df[non_blank_cols]
    return df


def get_nonzero_indices(df, cols: list[str]):
    df = df[cols]
    filtered_df = df[(df > 0).all(axis=1) & (~pd.isna(df)).all(axis=1)]
    return filtered_df.index


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
    
    