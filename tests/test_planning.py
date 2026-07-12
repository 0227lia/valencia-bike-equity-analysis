import pandas as pd

from planning import select_counterfactual_review_areas


def test_counterfactual_plan_respects_neighborhood_caps_and_improves_the_frontier():
    planning_grid = pd.DataFrame(
        {
            "codbar": [1, 1, 2, 2],
            "neighborhood": ["A", "A", "B", "B"],
            "district": ["North", "North", "South", "South"],
            "grid_point": [0, 1, 0, 1],
            "lat": [39.4700, 39.4710, 39.4800, 39.4810],
            "lon": [-0.3800, -0.3800, -0.3600, -0.3600],
            "nearest_bike_parking_m": [650.0, 500.0, 700.0, 550.0],
            "is_underserved": [True, True, True, True],
        }
    )
    scores = pd.DataFrame(
        {
            "codbar": [1, 2],
            "priority_score": [0.9, 0.5],
            "top_10_probability": [0.9, 0.4],
            "expected_rank": [1.2, 4.0],
        }
    )

    candidates, frontier = select_counterfactual_review_areas(
        planning_grid,
        scores,
        target_distance_meters=250,
        max_candidates=2,
        max_per_neighborhood=1,
        min_separation_meters=100,
        budgets=(0, 1, 2),
    )

    assert len(candidates) == 2
    assert candidates["codbar"].nunique() == 2
    assert candidates["marginal_weighted_gap_reduction_m"].gt(0).all()
    assert frontier["weighted_gap_reduction_share"].is_monotonic_increasing
    assert frontier["underserved_points_covered"].is_monotonic_increasing
