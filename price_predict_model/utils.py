from datetime import datetime

import numpy as np

import shared
from instances_and_definitions import ModifiableListing


def form_column_name(col_name: str) -> str:
    return col_name.lower().replace(' ', '_')


def weighted_mse(y_true, y_pred, overprediction_weight, underprediction_weight):
    """
    Custom MSE function that weights overpredictions and underpredictions differently.
    - Overpredictions are weighted more heavily.
    - Underpredictions are weighted less heavily.

    Args:
        y_true: Array of true (observed) values.
        y_pred: Array of predicted values.
        overprediction_weight: Weight for overpredictions (greater than true value).
        underprediction_weight: Weight for underpredictions (less than true value).

    Returns:
        Weighted Mean Squared Error.
    """

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    # Calculate the error (difference between predicted and true values)
    error = y_pred - y_true

    # Create weights based on whether the error is positive (overprediction) or negative (underprediction)
    weights = np.where(error > 0, overprediction_weight, underprediction_weight)

    # Calculate weighted squared error
    weighted_squared_error = weights * np.square(error)

    # Compute the mean of the weighted squared errors
    weighted_mse_value = np.mean(weighted_squared_error)

    return weighted_mse_value


def _flatten_listing(listing: ModifiableListing) -> dict:
    flattened_properties = _flatten_listing_properties(listing)
    dt_date_fetched = datetime.strptime(listing.date_fetched, "%m-%d-%Y")
    exalts_price = shared.currency_converter.convert_to_exalts(currency=listing.currency,
                                                               currency_amount=listing.currency_amount,
                                                               relevant_date=dt_date_fetched)

    flattened_data = {
        'minutes_since_listed': listing.minutes_since_listed,
        'minutes_since_league_start': listing.minutes_since_league_start,
        'exalts': exalts_price,
        'open_prefixes': listing.open_prefixes,
        'open_suffixes': listing.open_suffixes,
        'rarity': listing.rarity,
        'corrupted': listing.corrupted,
        **flattened_properties
    }

    # Split up hybrid mods and average their value ranges. No known value ranges are not averageable
    summed_sub_mods = sum_sub_mod_values(listing)
    flattened_data.update(summed_sub_mods)

    skills_dict = {item_skill.name: item_skill.level for item_skill in listing.item_skills}
    flattened_data.update(skills_dict)

    flattened_data['max_quality_pdps'] = utils.calculate_max_quality_pdps(flattened_data)
    flattened_data['edps'] = utils.calculate_elemental_dps(flattened_data)

    for col in [*self.__class__._aggregate_remove_cols]:
        flattened_data.pop(col, None)

    # Some columns have just one letter - not sure why but need to find out
    cols_to_remove = [col for col in flattened_data if len(col) == 1]
    for col in cols_to_remove:
        logging.error(f"Found 1-length attribute name {cols_to_remove} for listing {listing.__dict__}")
        flattened_data.pop(col)

    return flattened_data
