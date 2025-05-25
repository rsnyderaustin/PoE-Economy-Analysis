import pandas as pd


def normalize_column_name(col: str | tuple) -> str:
    return f"{col[0]}_{col[1]}" if isinstance(col, tuple) else col


def _determine_number_of_infrequent_values(df, col):
    most_frequent_value = df[col].mode()[0]
    non_constant_count = df[df[col] != most_frequent_value].count()


def filter_out_empty_rows(df):
    non_negative_rows = (df != 0).all(axis=1)
    no_nans = ~df.isna().any(axis=1)

    filtered_df = df[non_negative_rows & no_nans]

    return filtered_df
