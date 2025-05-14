import numpy as np

from instances_and_definitions import ModifiableListing


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

    # Sometimes there is overlap in regular mods with socketer mods, so including them is the easiest way to provide
    # their effect to the AI training data
    for socketer in listing.socketers:
        col_name = socketer.sanitized_socketer_text
        if socketer.actual_values:
            avg_value = sum(socketer.actual_values) / len(socketer.actual_values)
            if col_name not in summed_sub_mods:
                summed_sub_mods[col_name] = avg_value
            else:
                summed_sub_mods[col_name] += avg_value
        else:
            summed_sub_mods[col_name] = 1

    return summed_sub_mods


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


def calculate_max_quality_pdps(listing_data: dict):
    quality = listing_data.get('Quality', 0)
    damage = listing_data.get('Physical Damage', 0)
    attacks_per_second = listing_data.get('Attacks per Second', 0)

    current_multiplier = 1 + (quality / 100)
    max_multiplier = 1.20

    # Calculate the base damage and then the 20% quality damage
    base_damage = damage / current_multiplier
    max_quality_damage = base_damage * max_multiplier

    max_quality_pdps = max_quality_damage * attacks_per_second
    return max_quality_pdps


def calculate_elemental_dps(listing_data: dict):
    cold_damage = listing_data.get('Cold Damage', 0)
    fire_damage = listing_data.get('Fire Damage', 0)
    lightning_damage = listing_data.get('Lightning Damage', 0)
    attacks_per_second = listing_data.get('Attacks per Second', 0)

    edps = (cold_damage + fire_damage + lightning_damage) * attacks_per_second
    return edps

