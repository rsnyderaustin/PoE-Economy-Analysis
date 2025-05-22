import logging
from abc import ABC
from datetime import datetime

import pandas as pd

import shared
from instances_and_definitions import ModifiableListing
from shared import shared_utils
from . import utils


class ListingsDataProcessor(ListingsClass):

    @staticmethod
    def flatten_listings(listings: list[ModifiableListing]) -> dict:
        logging.info(f"Flattening {len(listings)} listings.")
        listings_data = dict()
        rows = 0
        for listing in listings:
            new_listing_data = ListingFlattener.flatten_listing(listing)

            new_cols = [col for col in new_listing_data if col not in listings_data]
            new_cols_dict = {col: [None] * rows for col in new_cols}
            listings_data.update(new_cols_dict)

            for col in listings_data:
                new_val = new_listing_data.get(col, None)
                listings_data[col].append(new_val)

            rows += 1

        return listings_data

    @classmethod
    def prepare_flattened_listings_data_for_model(cls, data: dict) -> pd.DataFrame:
        df = pd.DataFrame(data)

        select_dtype_cols = [col for col in cls._select_col_types if col in df.columns]
        for col in select_dtype_cols:
            dtype = cls._select_col_types[col]
            df[col] = df[col].astype(dtype)

        abnormal_type_cols = [col for col in df.columns
                              if col not in cls._select_col_types
                              and df[col].dtype not in ['int64', 'float64', 'bool', 'category']]
        for col in abnormal_type_cols:
            df[col] = df[col].astype('float64')

        df = df.select_dtypes(include=['int64', 'float64', 'bool', 'category'])

        return df
