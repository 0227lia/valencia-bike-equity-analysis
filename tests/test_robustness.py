import pandas as pd

from robustness import sample_weight_robustness


def test_weight_robustness_returns_bounded_probabilities_and_reproducible_results():
    scores = pd.DataFrame(
        {
            "codbar": [1, 2, 3, 4],
            "neighborhood": ["A", "B", "C", "D"],
            "district": ["North", "North", "South", "South"],
            "priority_score": [0.9, 0.7, 0.5, 0.2],
            "vulnerability_pressure": [1.0, 0.7, 0.4, 0.1],
            "capacity_gap": [0.9, 0.6, 0.5, 0.1],
            "accessibility_gap": [0.8, 0.7, 0.3, 0.2],
            "underserved_gap": [0.8, 0.6, 0.4, 0.1],
        }
    )
    components = {
        "vulnerability": "vulnerability_pressure",
        "capacity": "capacity_gap",
        "accessibility": "accessibility_gap",
        "underserved": "underserved_gap",
    }
    weights = {"vulnerability": 0.4, "capacity": 0.3, "accessibility": 0.2, "underserved": 0.1}

    first, summary = sample_weight_robustness(
        scores,
        components,
        weights,
        samples=500,
        concentration=40,
        random_state=42,
    )
    second, _ = sample_weight_robustness(
        scores,
        components,
        weights,
        samples=500,
        concentration=40,
        random_state=42,
    )

    pd.testing.assert_frame_equal(first, second)
    assert summary["samples"] == 500
    assert first["base_rank"].tolist() == [1, 2, 3, 4]
    assert first["top_10_probability"].between(0, 1).all()
    assert first["rank_p05"].ge(1).all()
    assert first["rank_p95"].le(len(scores)).all()
