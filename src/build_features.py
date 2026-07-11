import json
from pathlib import Path

import numpy as np
import pandas as pd

from config import (
    ACCESSIBILITY_GRID_PATH,
    BIKE_PARKING_ENRICHED_PATH,
    BIKE_PARKING_PATH,
    BIKE_RAW_PATH,
    CANDIDATE_LOCATIONS_PATH,
    DEFAULT_PRIORITY_WEIGHTS,
    EQUITY_SCORES_PATH,
    GRID_STEP_METERS,
    MAX_CANDIDATES,
    MAX_CANDIDATES_PER_NEIGHBORHOOD,
    MIN_CANDIDATE_DISTANCE_METERS,
    NEIGHBORHOODS_PATH,
    NEIGHBORHOODS_RAW_PATH,
    PRIORITY_SCENARIOS,
    PROCESSED_DIR,
    SENSITIVITY_REPORT_PATH,
    TARGET_DISTANCE_METERS,
)
from fetch_data import main as fetch_data
from geo_utils import (
    geometry_covers_point,
    grid_points_in_geometry,
    haversine_meters,
    nearest_distance_meters,
    shape_geometry,
    utm_to_latlon,
)

PRIORITY_COMPONENT_COLUMNS = {
    "vulnerability": "vulnerability_pressure",
    "capacity": "capacity_gap",
    "accessibility": "accessibility_gap",
    "underserved": "underserved_gap",
}


def ensure_raw_data() -> None:
    if not BIKE_RAW_PATH.exists() or not NEIGHBORHOODS_RAW_PATH.exists():
        fetch_data()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_bike_parking() -> pd.DataFrame:
    payload = load_json(BIKE_RAW_PATH)
    rows = []

    for feature in payload["features"]:
        attributes = feature["attributes"]
        geometry = feature["geometry"]
        lat, lon = utm_to_latlon(geometry["x"], geometry["y"])
        rows.append(
            {
                "objectid": attributes["objectid"],
                "parking_type": attributes.get("tipo"),
                "spaces": int(attributes.get("numplazas") or 0),
                "x_utm": geometry["x"],
                "y_utm": geometry["y"],
                "lat": lat,
                "lon": lon,
            }
        )

    bike_parking = pd.DataFrame(rows).sort_values("objectid")
    bike_parking.to_csv(BIKE_PARKING_PATH, index=False)
    return bike_parking


def normalize_neighborhoods() -> tuple[pd.DataFrame, list[dict]]:
    geojson = load_json(NEIGHBORHOODS_RAW_PATH)
    rows = []
    features = []

    for feature in geojson["features"]:
        props = feature["properties"]
        centroid = props.get("geo_point_2d", {})
        codbar = int(props["codbar"])

        rows.append(
            {
                "codbar": codbar,
                "neighborhood": props["nombre"],
                "district": props["distrito"],
                "ind_equip": float(props["ind_equip"]),
                "ind_dem": float(props["ind_dem"]),
                "ind_econom": float(props["ind_econom"]),
                "ind_global": float(props["ind_global"]),
                "vul_global": props["vul_global"],
                "area_m2": float(props["shape_area"]),
                "area_km2": float(props["shape_area"]) / 1_000_000,
                "centroid_lat": float(centroid["lat"]),
                "centroid_lon": float(centroid["lon"]),
            }
        )
        features.append({"codbar": codbar, "geometry": feature["geometry"]})

    neighborhoods = pd.DataFrame(rows).sort_values("codbar")
    neighborhoods.to_csv(NEIGHBORHOODS_PATH, index=False)
    return neighborhoods, features


def assign_bike_parking_to_neighborhoods(
    bike_parking: pd.DataFrame,
    neighborhood_features: list[dict],
) -> pd.DataFrame:
    enriched_rows = []
    neighborhood_shapes = [
        (feature["codbar"], shape_geometry(feature["geometry"])) for feature in neighborhood_features
    ]

    for row in bike_parking.to_dict("records"):
        assigned_codbar = None
        for codbar, geometry in neighborhood_shapes:
            if geometry_covers_point(geometry, row["lon"], row["lat"]):
                assigned_codbar = codbar
                break

        enriched_rows.append({**row, "codbar": assigned_codbar})

    enriched = pd.DataFrame(enriched_rows)
    enriched.to_csv(BIKE_PARKING_ENRICHED_PATH, index=False)
    return enriched


def normalize_series(values: pd.Series, inverse: bool = False) -> pd.Series:
    values = values.astype(float)
    if inverse:
        values = values.max() - values
    min_value = values.min()
    max_value = values.max()
    if np.isclose(max_value, min_value):
        return pd.Series(np.zeros(len(values)), index=values.index)
    return (values - min_value) / (max_value - min_value)


def calculate_priority_score(
    scores: pd.DataFrame,
    weights: dict[str, float],
) -> pd.Series:
    if set(weights) != set(PRIORITY_COMPONENT_COLUMNS):
        raise ValueError(f"Weights must contain {sorted(PRIORITY_COMPONENT_COLUMNS)}")
    if not np.isclose(sum(weights.values()), 1.0):
        raise ValueError("Priority weights must sum to 1")
    if any(weight < 0 for weight in weights.values()):
        raise ValueError("Priority weights cannot be negative")

    result = pd.Series(0.0, index=scores.index)
    for component, column in PRIORITY_COMPONENT_COLUMNS.items():
        result += weights[component] * scores[column]
    return result


def build_accessibility_grid(
    neighborhoods: pd.DataFrame,
    neighborhood_features: list[dict],
    bike_parking: pd.DataFrame,
) -> pd.DataFrame:
    bike_points = list(zip(bike_parking["lat"], bike_parking["lon"], strict=True))
    grid_rows = []

    for feature in neighborhood_features:
        codbar = feature["codbar"]
        neighborhood = neighborhoods.loc[neighborhoods["codbar"] == codbar].iloc[0]
        points = grid_points_in_geometry(
            feature["geometry"],
            step_meters=GRID_STEP_METERS,
            center_lat=neighborhood["centroid_lat"],
        )

        for point_index, (lat, lon) in enumerate(points):
            distance = nearest_distance_meters(lat, lon, bike_points)
            grid_rows.append(
                {
                    "codbar": codbar,
                    "neighborhood": neighborhood["neighborhood"],
                    "district": neighborhood["district"],
                    "grid_point": point_index,
                    "lat": lat,
                    "lon": lon,
                    "nearest_bike_parking_m": round(distance, 1),
                    "is_underserved": distance > TARGET_DISTANCE_METERS,
                }
            )

    grid = pd.DataFrame(grid_rows)
    grid.to_csv(ACCESSIBILITY_GRID_PATH, index=False)
    return grid


def build_equity_scores(
    neighborhoods: pd.DataFrame,
    bike_parking_enriched: pd.DataFrame,
    accessibility_grid: pd.DataFrame,
) -> pd.DataFrame:
    bike_agg = (
        bike_parking_enriched.dropna(subset=["codbar"])
        .assign(codbar=lambda df: df["codbar"].astype(int))
        .groupby("codbar", as_index=False)
        .agg(
            bike_parking_points=("objectid", "count"),
            bike_parking_spaces=("spaces", "sum"),
        )
    )

    grid_agg = accessibility_grid.groupby("codbar", as_index=False).agg(
        grid_points=("grid_point", "count"),
        underserved_share=("is_underserved", "mean"),
        median_nearest_bike_parking_m=("nearest_bike_parking_m", "median"),
        p90_nearest_bike_parking_m=("nearest_bike_parking_m", lambda x: np.percentile(x, 90)),
    )

    scores = (
        neighborhoods.merge(bike_agg, on="codbar", how="left")
        .merge(grid_agg, on="codbar", how="left")
        .fillna(
            {
                "bike_parking_points": 0,
                "bike_parking_spaces": 0,
                "grid_points": 0,
                "underserved_share": 1,
                "median_nearest_bike_parking_m": 999,
                "p90_nearest_bike_parking_m": 999,
            }
        )
    )

    scores["spaces_per_km2"] = scores["bike_parking_spaces"] / scores["area_km2"]
    scores["points_per_km2"] = scores["bike_parking_points"] / scores["area_km2"]

    scores["vulnerability_pressure"] = normalize_series(scores["ind_global"], inverse=True)
    scores["capacity_gap"] = normalize_series(scores["spaces_per_km2"], inverse=True)
    scores["accessibility_gap"] = normalize_series(scores["p90_nearest_bike_parking_m"])
    scores["underserved_gap"] = normalize_series(scores["underserved_share"])

    scores["priority_score"] = calculate_priority_score(scores, DEFAULT_PRIORITY_WEIGHTS)

    scores = scores.sort_values("priority_score", ascending=False)
    scores.to_csv(EQUITY_SCORES_PATH, index=False)
    return scores


def build_sensitivity_analysis(scores: pd.DataFrame) -> pd.DataFrame:
    default_ranks = scores["priority_score"].rank(ascending=False, method="average")
    default_top = set(scores.nlargest(10, "priority_score")["codbar"].astype(int))
    rows = []

    for scenario, weights in PRIORITY_SCENARIOS.items():
        scenario_scores = calculate_priority_score(scores, weights)
        scenario_ranks = scenario_scores.rank(ascending=False, method="average")
        scenario_top = set(scores.loc[scenario_scores.nlargest(10).index, "codbar"].astype(int))
        overlap_count = len(default_top & scenario_top)

        rows.append(
            {
                "scenario": scenario,
                "rank_correlation_with_default": round(default_ranks.corr(scenario_ranks), 4),
                "top_10_overlap_count": overlap_count,
                "top_10_overlap_share": overlap_count / 10,
                **{f"weight_{name}": value for name, value in weights.items()},
            }
        )

    result = pd.DataFrame(rows)
    SENSITIVITY_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(SENSITIVITY_REPORT_PATH, index=False)
    return result


def build_candidate_locations(
    accessibility_grid: pd.DataFrame,
    equity_scores: pd.DataFrame,
) -> pd.DataFrame:
    candidates = (
        accessibility_grid[accessibility_grid["is_underserved"]]
        .merge(equity_scores[["codbar", "priority_score"]], on="codbar", how="left")
        .copy()
    )
    candidates["distance_pressure"] = normalize_series(candidates["nearest_bike_parking_m"])
    candidates["candidate_score"] = (
        0.70 * candidates["priority_score"] + 0.30 * candidates["distance_pressure"]
    )
    candidates = candidates.sort_values("candidate_score", ascending=False)

    selected = []
    selected_by_neighborhood: dict[int, int] = {}
    for row in candidates.to_dict("records"):
        codbar = int(row["codbar"])
        if selected_by_neighborhood.get(codbar, 0) >= MAX_CANDIDATES_PER_NEIGHBORHOOD:
            continue

        far_enough = all(
            haversine_meters(row["lat"], row["lon"], item["lat"], item["lon"])
            >= MIN_CANDIDATE_DISTANCE_METERS
            for item in selected
        )
        if far_enough:
            selected.append(row)
            selected_by_neighborhood[codbar] = selected_by_neighborhood.get(codbar, 0) + 1
        if len(selected) >= MAX_CANDIDATES:
            break

    result = pd.DataFrame(selected)
    result.insert(0, "candidate_rank", range(1, len(result) + 1))
    result.to_csv(CANDIDATE_LOCATIONS_PATH, index=False)
    return result


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    ensure_raw_data()

    bike_parking = normalize_bike_parking()
    neighborhoods, neighborhood_features = normalize_neighborhoods()
    bike_parking_enriched = assign_bike_parking_to_neighborhoods(bike_parking, neighborhood_features)
    accessibility_grid = build_accessibility_grid(neighborhoods, neighborhood_features, bike_parking)
    equity_scores = build_equity_scores(neighborhoods, bike_parking_enriched, accessibility_grid)
    sensitivity = build_sensitivity_analysis(equity_scores)
    candidate_locations = build_candidate_locations(accessibility_grid, equity_scores)

    print(f"Processed {len(neighborhoods)} neighborhoods")
    print(f"Processed {len(bike_parking)} bike parking points")
    print(f"Generated {len(accessibility_grid)} accessibility grid points")
    print(f"Selected {len(candidate_locations)} candidate locations")
    print(f"Evaluated {len(sensitivity)} priority-weight scenarios")


if __name__ == "__main__":
    main()
