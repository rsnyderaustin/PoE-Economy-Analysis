
import numpy as np


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