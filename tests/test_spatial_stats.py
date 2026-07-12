import numpy as np
import pandas as pd
import pytest

from spatial_stats import knn_row_standardized_weights, morans_i, spatial_priority_diagnostics


def spatial_scores() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "codbar": [1, 2, 3, 4, 5, 6],
            "neighborhood": list("ABCDEF"),
            "district": ["North"] * 3 + ["South"] * 3,
            "centroid_lat": [39.47, 39.47, 39.47, 39.48, 39.48, 39.48],
            "centroid_lon": [-0.38, -0.37, -0.36, -0.38, -0.37, -0.36],
            "priority_score": [0.1, 0.2, 0.3, 0.7, 0.8, 0.9],
        }
    )


def test_knn_weights_are_row_standardized_and_morans_i_is_finite():
    scores = spatial_scores()
    weights = knn_row_standardized_weights(
        scores[["centroid_lat", "centroid_lon"]].to_numpy(),
        neighbors=2,
    )

    assert weights.shape == (6, 6)
    assert np.allclose(weights.sum(axis=1), 1)
    assert np.allclose(np.diag(weights), 0)
    assert np.isfinite(morans_i(scores["priority_score"].to_numpy(), weights))


def test_spatial_diagnostics_are_reproducible_and_descriptive():
    first_clusters, first_diagnostics = spatial_priority_diagnostics(
        spatial_scores(),
        neighbors=2,
        permutations=99,
        random_state=42,
    )
    second_clusters, second_diagnostics = spatial_priority_diagnostics(
        spatial_scores(),
        neighbors=2,
        permutations=99,
        random_state=42,
    )

    pd.testing.assert_frame_equal(first_clusters, second_clusters)
    assert first_diagnostics == second_diagnostics
    assert first_diagnostics["permutation_p_value_two_sided"] == pytest.approx(
        first_diagnostics["permutation_p_value_two_sided"]
    )
    assert set(first_clusters["spatial_quadrant"]).issubset(
        {"high-high", "high-low", "low-high", "low-low"}
    )
