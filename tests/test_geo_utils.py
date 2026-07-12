import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from geo_utils import (
    grid_points_in_geometry,
    haversine_meters,
    nearest_distance_meters,
    nearest_distances_meters,
    point_in_geojson_geometry,
    utm_to_latlon,
)


def test_utm_to_latlon_valencia_range():
    lat, lon = utm_to_latlon(725899.055, 4370112.689)
    assert lat == pytest.approx(39.45097, abs=0.0001)
    assert lon == pytest.approx(-0.37465, abs=0.0001)


def test_haversine_zero_distance():
    assert haversine_meters(39.47, -0.37, 39.47, -0.37) == 0


def test_point_in_geojson_polygon():
    square = {
        "type": "Polygon",
        "coordinates": [
            [
                [-1.0, 39.0],
                [1.0, 39.0],
                [1.0, 41.0],
                [-1.0, 41.0],
                [-1.0, 39.0],
            ]
        ],
    }
    assert point_in_geojson_geometry(0.0, 40.0, square)
    assert not point_in_geojson_geometry(2.0, 40.0, square)


def test_polygon_hole_is_not_covered():
    polygon_with_hole = {
        "type": "Polygon",
        "coordinates": [
            [[-1, 39], [1, 39], [1, 41], [-1, 41], [-1, 39]],
            [[-0.2, 39.8], [0.2, 39.8], [0.2, 40.2], [-0.2, 40.2], [-0.2, 39.8]],
        ],
    }

    assert point_in_geojson_geometry(0.8, 40.0, polygon_with_hole)
    assert not point_in_geojson_geometry(0.0, 40.0, polygon_with_hole)


def test_small_polygon_receives_representative_grid_point():
    small_polygon = {
        "type": "Polygon",
        "coordinates": [
            [
                [-0.3710, 39.4700],
                [-0.3709, 39.4700],
                [-0.3709, 39.4701],
                [-0.3710, 39.4701],
                [-0.3710, 39.4700],
            ]
        ],
    }

    points = grid_points_in_geometry(small_polygon, step_meters=300, center_lat=39.47)

    assert len(points) == 1
    lat, lon = points[0]
    assert point_in_geojson_geometry(lon, lat, small_polygon)


def test_nearest_distance_requires_candidates():
    with pytest.raises(ValueError, match="at least one"):
        nearest_distance_meters(39.47, -0.37, [])


def test_vectorized_nearest_distances_match_scalar_calculation():
    points = [(39.4700, -0.3700), (39.4750, -0.3650)]
    candidates = [(39.4700, -0.3700), (39.4800, -0.3600)]

    result = nearest_distances_meters(
        [point[0] for point in points],
        [point[1] for point in points],
        candidates,
    )

    expected = [nearest_distance_meters(*point, candidates) for point in points]
    assert result.tolist() == pytest.approx(expected)
