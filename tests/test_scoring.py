import pandas as pd
import pytest

from build_features import calculate_priority_score, normalize_series


def component_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "vulnerability_pressure": [0.0, 1.0],
            "capacity_gap": [0.2, 0.8],
            "accessibility_gap": [0.4, 0.6],
            "underserved_gap": [0.6, 0.4],
        }
    )


def test_normalize_series_and_inverse():
    values = pd.Series([10, 20, 30])

    assert normalize_series(values).tolist() == [0.0, 0.5, 1.0]
    assert normalize_series(values, inverse=True).tolist() == [1.0, 0.5, 0.0]


def test_priority_score_uses_declared_weights():
    weights = {
        "vulnerability": 0.4,
        "capacity": 0.3,
        "accessibility": 0.2,
        "underserved": 0.1,
    }

    result = calculate_priority_score(component_frame(), weights)

    assert result.tolist() == pytest.approx([0.2, 0.8])


@pytest.mark.parametrize(
    "weights",
    [
        {"vulnerability": 1.0},
        {
            "vulnerability": 0.4,
            "capacity": 0.3,
            "accessibility": 0.2,
            "underserved": 0.2,
        },
        {
            "vulnerability": 0.4,
            "capacity": 0.3,
            "accessibility": 0.4,
            "underserved": -0.1,
        },
    ],
)
def test_priority_score_rejects_invalid_weights(weights):
    with pytest.raises(ValueError):
        calculate_priority_score(component_frame(), weights)
