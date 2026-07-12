"""Monte Carlo robustness diagnostics for the additive priority model."""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd


def sample_weight_robustness(
    scores: pd.DataFrame,
    component_columns: Mapping[str, str],
    reference_weights: Mapping[str, float],
    *,
    samples: int,
    concentration: float,
    random_state: int,
) -> tuple[pd.DataFrame, dict[str, float | int]]:
    """Estimate ranking stability when policy weights vary around the base scenario.

    Weights are sampled from a Dirichlet distribution centred on the declared base
    weights. The concentration controls dispersion: higher values mean less policy
    variation around the base scenario.
    """
    if samples < 100:
        raise ValueError("samples must be at least 100")
    if concentration <= 0:
        raise ValueError("concentration must be positive")

    component_names = list(component_columns)
    if set(reference_weights) != set(component_names):
        raise ValueError("reference_weights must match component_columns")

    base_weight_values = np.asarray([reference_weights[name] for name in component_names], dtype=float)
    if np.any(base_weight_values <= 0) or not np.isclose(base_weight_values.sum(), 1.0):
        raise ValueError("reference_weights must be positive and sum to 1")

    values = scores[[component_columns[name] for name in component_names]].to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("Priority components must be finite")

    generator = np.random.default_rng(random_state)
    sampled_weights = generator.dirichlet(base_weight_values * concentration, size=samples)
    sampled_scores = values @ sampled_weights.T

    # argsort(argsort()) gives a deterministic ordinal rank for every simulation.
    ranks = np.argsort(np.argsort(-sampled_scores, axis=0), axis=0) + 1
    base_rank = scores["priority_score"].rank(ascending=False, method="first").astype(int).to_numpy()

    result = scores[["codbar", "neighborhood", "district", "priority_score"]].copy()
    result["base_rank"] = base_rank
    result["expected_priority_score"] = sampled_scores.mean(axis=1)
    result["priority_score_p05"] = np.quantile(sampled_scores, 0.05, axis=1)
    result["priority_score_p95"] = np.quantile(sampled_scores, 0.95, axis=1)
    result["expected_rank"] = ranks.mean(axis=1)
    result["rank_p05"] = np.quantile(ranks, 0.05, axis=1)
    result["rank_p50"] = np.quantile(ranks, 0.50, axis=1)
    result["rank_p95"] = np.quantile(ranks, 0.95, axis=1)
    result["rank_interval_width"] = result["rank_p95"] - result["rank_p05"]
    result["top_1_probability"] = (ranks == 1).mean(axis=1)
    result["top_5_probability"] = (ranks <= 5).mean(axis=1)
    result["top_10_probability"] = (ranks <= 10).mean(axis=1)
    result = result.sort_values(["base_rank", "codbar"]).reset_index(drop=True)

    summary: dict[str, float | int] = {
        "samples": samples,
        "dirichlet_concentration": concentration,
        "random_state": random_state,
    }
    for index, name in enumerate(component_names):
        summary[f"base_weight_{name}"] = float(base_weight_values[index])
        summary[f"sampled_weight_mean_{name}"] = float(sampled_weights[:, index].mean())
        summary[f"sampled_weight_std_{name}"] = float(sampled_weights[:, index].std(ddof=0))

    return result, summary
