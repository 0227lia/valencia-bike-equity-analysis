"""Counterfactual screening plan for potential bike-parking review areas."""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd

from geo_utils import EARTH_RADIUS_METERS


def pairwise_haversine_meters(origins: np.ndarray, destinations: np.ndarray) -> np.ndarray:
    """Return great-circle distances for ``(lat, lon)`` origin and destination arrays."""
    origin_latitudes = np.radians(origins[:, 0])[:, None]
    origin_longitudes = np.radians(origins[:, 1])[:, None]
    destination_latitudes = np.radians(destinations[:, 0])[None, :]
    destination_longitudes = np.radians(destinations[:, 1])[None, :]
    delta_latitudes = destination_latitudes - origin_latitudes
    delta_longitudes = destination_longitudes - origin_longitudes
    haversine_a = (
        np.sin(delta_latitudes / 2) ** 2
        + np.cos(origin_latitudes)
        * np.cos(destination_latitudes)
        * np.sin(delta_longitudes / 2) ** 2
    )
    return 2 * EARTH_RADIUS_METERS * np.arctan2(np.sqrt(haversine_a), np.sqrt(1 - haversine_a))


def _eligible_candidate_indices(
    candidates: pd.DataFrame,
    selected_indices: Iterable[int],
    selected_by_neighborhood: dict[int, int],
    *,
    max_per_neighborhood: int,
    min_separation_meters: float,
) -> np.ndarray:
    indices = np.arange(len(candidates))
    eligible = np.ones(len(candidates), dtype=bool)
    selected_indices = list(selected_indices)
    eligible[selected_indices] = False

    neighborhood_counts = candidates["codbar"].map(selected_by_neighborhood).fillna(0).to_numpy()
    eligible &= neighborhood_counts < max_per_neighborhood

    if selected_indices:
        candidate_coordinates = candidates[["lat", "lon"]].to_numpy(dtype=float)
        selected_coordinates = candidate_coordinates[selected_indices]
        distance_to_selection = pairwise_haversine_meters(candidate_coordinates, selected_coordinates)
        eligible &= (distance_to_selection >= min_separation_meters).all(axis=1)

    return indices[eligible]


def _target_equity_weights(targets: pd.DataFrame) -> np.ndarray:
    """Prioritise distance-gap reduction in higher-priority and more stable areas."""
    return 1 + 1.5 * targets["priority_score"].to_numpy(float) + 0.75 * targets[
        "top_10_probability"
    ].to_numpy(float)


def select_counterfactual_review_areas(
    planning_grid: pd.DataFrame,
    equity_scores: pd.DataFrame,
    *,
    target_distance_meters: float,
    max_candidates: int,
    max_per_neighborhood: int,
    min_separation_meters: float,
    budgets: tuple[int, ...],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Greedily select review areas by weighted reduction of straight-line distance gaps.

    A selected point is a modeled screening location, not a construction recommendation.
    Each step tests the effect of adding one point to the existing network and chooses
    the eligible candidate that most reduces weighted distance above the service target.
    """
    required_columns = {"codbar", "priority_score", "top_10_probability", "expected_rank"}
    missing = required_columns - set(equity_scores.columns)
    if missing:
        raise ValueError(f"equity_scores is missing required columns: {sorted(missing)}")

    targets = planning_grid.merge(
        equity_scores[["codbar", "priority_score", "top_10_probability", "expected_rank"]],
        on="codbar",
        how="left",
        validate="many_to_one",
    )
    if targets["priority_score"].isna().any():
        raise ValueError("Every planning-grid point must map to an equity score")

    candidates = targets.loc[targets["is_underserved"]].copy().reset_index(drop=True)
    if candidates.empty:
        raise ValueError("No underserved planning-grid points are available as candidate review areas")

    target_coordinates = targets[["lat", "lon"]].to_numpy(dtype=float)
    candidate_coordinates = candidates[["lat", "lon"]].to_numpy(dtype=float)
    candidate_to_target_distances = pairwise_haversine_meters(candidate_coordinates, target_coordinates)

    current_distances = targets["nearest_bike_parking_m"].to_numpy(dtype=float)
    target_weights = _target_equity_weights(targets)
    baseline_gap = np.maximum(current_distances - target_distance_meters, 0)
    baseline_weighted_gap = float((baseline_gap * target_weights).sum())
    baseline_underserved_count = int((current_distances > target_distance_meters).sum())

    selected_indices: list[int] = []
    selected_by_neighborhood: dict[int, int] = {}
    selected_rows: list[dict[str, object]] = []
    trajectory: list[dict[str, float | int]] = [
        {
            "selected_candidates": 0,
            "underserved_points_remaining": baseline_underserved_count,
            "underserved_points_covered": 0,
            "underserved_reduction_share": 0.0,
            "weighted_gap_reduction_m": 0.0,
            "weighted_gap_reduction_share": 0.0,
        }
    ]

    for candidate_rank in range(1, max_candidates + 1):
        eligible_indices = _eligible_candidate_indices(
            candidates,
            selected_indices,
            selected_by_neighborhood,
            max_per_neighborhood=max_per_neighborhood,
            min_separation_meters=min_separation_meters,
        )
        if not len(eligible_indices):
            break

        candidate_distances = candidate_to_target_distances[eligible_indices]
        future_distances = np.minimum(current_distances[None, :], candidate_distances)
        current_gap = np.maximum(current_distances - target_distance_meters, 0)
        future_gaps = np.maximum(future_distances - target_distance_meters, 0)
        weighted_gains = ((current_gap[None, :] - future_gaps) * target_weights[None, :]).sum(axis=1)

        # Stable tie-breaking: greater current deficit, then higher neighborhood score,
        # then lower original row position.
        candidate_priority = candidates.iloc[eligible_indices]["priority_score"].to_numpy(float)
        candidate_deficit = candidates.iloc[eligible_indices]["nearest_bike_parking_m"].to_numpy(float)
        sort_order = np.lexsort((eligible_indices, -candidate_priority, -candidate_deficit, -weighted_gains))
        best_position = int(sort_order[0])
        selected_index = int(eligible_indices[best_position])
        future_distance = future_distances[best_position]
        selected_candidate = candidates.iloc[selected_index]

        before_underserved = current_distances > target_distance_meters
        after_underserved = future_distance > target_distance_meters
        marginal_newly_served = int((before_underserved & ~after_underserved).sum())
        marginal_weighted_gain = float(weighted_gains[best_position])
        current_distances = future_distance
        selected_indices.append(selected_index)

        codbar = int(selected_candidate["codbar"])
        selected_by_neighborhood[codbar] = selected_by_neighborhood.get(codbar, 0) + 1
        remaining_underserved = int(after_underserved.sum())
        remaining_gap = np.maximum(current_distances - target_distance_meters, 0)
        weighted_gap_remaining = float((remaining_gap * target_weights).sum())
        cumulative_weighted_gain = baseline_weighted_gap - weighted_gap_remaining

        selected_rows.append(
            {
                "candidate_rank": candidate_rank,
                "candidate_type": "modeled_review_area",
                "codbar": codbar,
                "neighborhood": selected_candidate["neighborhood"],
                "district": selected_candidate["district"],
                "planning_grid_point": int(selected_candidate["grid_point"]),
                "lat": float(selected_candidate["lat"]),
                "lon": float(selected_candidate["lon"]),
                "nearest_bike_parking_m": float(selected_candidate["nearest_bike_parking_m"]),
                "priority_score": float(selected_candidate["priority_score"]),
                "top_10_probability": float(selected_candidate["top_10_probability"]),
                "expected_rank": float(selected_candidate["expected_rank"]),
                "marginal_newly_served_grid_points": marginal_newly_served,
                "marginal_weighted_gap_reduction_m": marginal_weighted_gain,
                "cumulative_underserved_points_covered": baseline_underserved_count - remaining_underserved,
                "cumulative_underserved_reduction_share": (
                    (baseline_underserved_count - remaining_underserved) / baseline_underserved_count
                ),
                "cumulative_weighted_gap_reduction_m": cumulative_weighted_gain,
                "cumulative_weighted_gap_reduction_share": cumulative_weighted_gain / baseline_weighted_gap,
            }
        )
        trajectory.append(
            {
                "selected_candidates": candidate_rank,
                "underserved_points_remaining": remaining_underserved,
                "underserved_points_covered": baseline_underserved_count - remaining_underserved,
                "underserved_reduction_share": (
                    (baseline_underserved_count - remaining_underserved) / baseline_underserved_count
                ),
                "weighted_gap_reduction_m": cumulative_weighted_gain,
                "weighted_gap_reduction_share": cumulative_weighted_gain / baseline_weighted_gap,
            }
        )

    selected = pd.DataFrame(selected_rows)
    frontier_rows = []
    for budget in sorted(set(budgets)):
        if budget < 0:
            raise ValueError("budgets cannot contain negative values")
        state = trajectory[min(budget, len(trajectory) - 1)]
        frontier_rows.append(
            {
                "budget": budget,
                "candidate_pool_size": len(candidates),
                "baseline_underserved_points": baseline_underserved_count,
                "baseline_weighted_distance_gap_m": baseline_weighted_gap,
                **state,
            }
        )

    return selected, pd.DataFrame(frontier_rows)
