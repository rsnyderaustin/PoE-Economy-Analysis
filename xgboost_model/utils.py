from pathlib import Path

import pandas as pd

from instances_and_definitions import ModifiableListing
from shared import PathProcessor


def form_column_name(col_name: str) -> str:
    return col_name.lower().replace(' ', '_')


def sum_sub_mod_values(listing: ModifiableListing):
    summed_sub_mods = {}
    for mod in listing.mods:
        for sub_mod in mod.sub_mods:
            col_name = form_column_name(sub_mod.sanitized_mod_text)
            if sub_mod.actual_values:
                avg_value = sum(sub_mod.actual_values) / len(sub_mod.actual_values)
                if sub_mod.mod_id not in summed_sub_mods:
                    summed_sub_mods[col_name] = avg_value
                else:
                    summed_sub_mods[col_name] += avg_value
            else:
                # If there is no value then it's just a static property (ex: "You cannot be poisoned"), and so
                # we assign it a 1 to indicate to the model that it's an active mod
                summed_sub_mods[col_name] = 1
    return summed_sub_mods


def count_socketers(listing: ModifiableListing) -> dict:
    socketer_counts = dict()
    for socketer_name in listing.socketers:
        if socketer_name not in socketer_counts:
            socketer_counts[socketer_name] = 0
        socketer_counts[socketer_name] += 1

    return socketer_counts


def fetch_currency_to_conversion() -> dict:
    currency_conversion_json_path = (
        PathProcessor(Path.cwd())
        .attach_file_path_endpoint('xgboost_model/training_data/currency_prices.csv')
        .path
    )
    currency_conversions = pd.read_csv(currency_conversion_json_path)
    currency_conversions['Date'] = pd.to_datetime(currency_conversions['Date'])
    most_recent_date = currency_conversions['Date'].max()
    recent_data = currency_conversions[currency_conversions['Date'] == most_recent_date]
    currency_to_exalts = pd.Series(recent_data['ExaltPerCurrency'].values,
                                   index=recent_data['Currency']).to_dict()
    return currency_to_exalts

