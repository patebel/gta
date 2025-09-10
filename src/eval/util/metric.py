import numpy as np


def compute_rmse(dict_a, dict_b):
    """
    Computes the root mean squared error between two dictionaries (with the same keys)
    containing percentage values.
    """
    differences = [(dict_a[k] - dict_b[k]) ** 2 for k in dict_a.keys()]
    return np.sqrt(np.mean(differences))
