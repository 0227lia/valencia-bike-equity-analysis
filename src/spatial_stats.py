"""Small, dependency-light spatial diagnostics for exploratory priority analysis."""

from __future__ import annotations

import numpy as np
import pandas as pd

from geo_utils import EARTH_RADIUS_METERS


def _haversine_distance_matrix(coordinates: np.ndarray) -> np.ndarray:
    latitudes = np.radians(coordinates[:, 0])[:, None]
    longitudes = np.radians(coordinates[:, 1])[:, None]
    delta_latitudes = latitudes.T - latitudes
    delta_longitudes = longitudes.T - longitudes
    haversine_a = (
        np.sin(delta_latitudes / 2) ** 2
        + np.cos(latitudes) * np.cos(latitudes.T) * np.sin(delta_longitudes / 2) ** 2
    )
    return 2 * EARTH_RADIUS_METERS * np.arctan2(np.sqrt(haversine_a), np.sqrt(1 - haversine_a))


def knn_row_standardized_weights(coordinates: np.ndarray, neighbors: int) -> np.ndarray:
    """Build a binary k-nearest-neighbour matrix with row-standardised weights."""
    count = len(coordinates)
    if count < 3:
        raise ValueError("At least three neighborhoods are required")
    if not 1 <= neighbors < count:
        raise ValueError("neighbors must be between 1 and n-1")

    distances = _haversine_distance_matrix(coordinates)
    np.fill_diagonal(distances, np.inf)
    nearest = np.argpartition(distances, kth=neighbors - 1, axis=1)[:, :neighbors]
    weights = np.zeros((count, count), dtype=float)
    weights[np.arange(count)[:, None], nearest] = 1.0
    return weights / weights.sum(axis=1, keepdims=True)


def morans_i(values: np.ndarray, weights: np.ndarray) -> float:
    values = np.asarray(values, dtype=float)
    centered = values - values.mean()
    denominator = float(centered @ centered)
    total_weight = float(weights.sum())
    if np.isclose(denominator, 0) or np.isclose(total_weight, 0):
        raise ValueError("Moran's I is undefined for constant values or empty weights")
    return float((len(values) / total_weight) * ((centered @ weights @ centered) / denominator))


def spatial_priority_diagnostics(
    scores: pd.DataFrame,
    *,
    neighbors: int,
    permutations: int,
    random_state: int,
) -> tuple[pd.DataFrame, dict[str, float | int]]:
    """Calculate global Moran's I and descriptive local quadrant labels.

    The labels classify each neighborhood relative to the global mean and the
    row-standardised spatial lag. They deliberately do not claim local significance.
    """
    if permutations < 99:
        raise ValueError("permutations must be at least 99")

    ordered = scores.sort_values("codbar").reset_index(drop=True)
    coordinates = ordered[["centroid_lat", "centroid_lon"]].to_numpy(dtype=float)
    values = ordered["priority_score"].to_numpy(dtype=float)
    weights = knn_row_standardized_weights(coordinates, neighbors)
    observed_i = morans_i(values, weights)

    centered = values - values.mean()
    standard_deviation = centered.std(ddof=0)
    standardized = centered / standard_deviation
    spatial_lag_z = weights @ standardized

    generator = np.random.default_rng(random_state)
    permuted_statistics = np.empty(permutations, dtype=float)
    for index in range(permutations):
        permuted_statistics[index] = morans_i(generator.permutation(values), weights)
    permutation_p_value = (np.count_nonzero(np.abs(permuted_statistics) >= abs(observed_i)) + 1) / (
        permutations + 1
    )

    quadrants = np.select(
        [
            (standardized >= 0) & (spatial_lag_z >= 0),
            (standardized >= 0) & (spatial_lag_z < 0),
            (standardized < 0) & (spatial_lag_z >= 0),
        ],
        ["high-high", "high-low", "low-high"],
        default="low-low",
    )

    clusters = ordered[["codbar", "neighborhood", "district", "priority_score"]].copy()
    clusters["priority_z_score"] = standardized
    clusters["spatial_lag_z_score"] = spatial_lag_z
    clusters["spatial_quadrant"] = quadrants
    clusters["knn_neighbors"] = neighbors

    diagnostics: dict[str, float | int] = {
        "variable": "priority_score",
        "neighborhoods": len(ordered),
        "knn_neighbors": neighbors,
        "permutations": permutations,
        "random_state": random_state,
        "morans_i": observed_i,
        "expected_i_under_randomization": -1 / (len(ordered) - 1),
        "permutation_p_value_two_sided": float(permutation_p_value),
        "permutation_i_p05": float(np.quantile(permuted_statistics, 0.05)),
        "permutation_i_p95": float(np.quantile(permuted_statistics, 0.95)),
    }
    return clusters, diagnostics
