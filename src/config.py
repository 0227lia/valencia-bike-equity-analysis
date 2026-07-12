from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
REPORT_DIR = ROOT / "reports"
FIGURE_DIR = REPORT_DIR / "figures"

BIKE_PARKING_URL = "https://geoportal.valencia.es/server/rest/services/OPENDATA/Trafico/MapServer/206/query"

VULNERABILITY_GEOJSON_URL = (
    "https://opendata.vlci.valencia.es/dataset/ca18278b-d040-4274-b9c7-c1a9daae54b9/"
    "resource/fd2ca0dc-5344-4aad-8934-2077a0bb120d/download/"
    "vulnerabilidad-por-barrios.geojson"
)

BIKE_RAW_PATH = RAW_DIR / "bike_parking_arcgis.json"
NEIGHBORHOODS_RAW_PATH = RAW_DIR / "neighborhood_vulnerability.geojson"
SOURCE_MANIFEST_PATH = RAW_DIR / "source_manifest.json"

NEIGHBORHOODS_PATH = PROCESSED_DIR / "neighborhoods.csv"
BIKE_PARKING_PATH = PROCESSED_DIR / "bike_parking.csv"
BIKE_PARKING_ENRICHED_PATH = PROCESSED_DIR / "bike_parking_enriched.csv"
ACCESSIBILITY_GRID_PATH = PROCESSED_DIR / "accessibility_grid.csv"
PLANNING_GRID_PATH = PROCESSED_DIR / "planning_grid.csv"
EQUITY_SCORES_PATH = PROCESSED_DIR / "neighborhood_equity_scores.csv"
CANDIDATE_LOCATIONS_PATH = PROCESSED_DIR / "candidate_locations.csv"
ROBUSTNESS_PATH = PROCESSED_DIR / "weight_robustness.csv"
SPATIAL_CLUSTERS_PATH = PROCESSED_DIR / "neighborhood_spatial_clusters.csv"
SENSITIVITY_REPORT_PATH = REPORT_DIR / "sensitivity_analysis.csv"
COVERAGE_FRONTIER_PATH = REPORT_DIR / "coverage_frontier.csv"
ROBUSTNESS_SUMMARY_PATH = REPORT_DIR / "robustness_summary.json"
SPATIAL_DIAGNOSTICS_PATH = REPORT_DIR / "spatial_diagnostics.json"

GRID_STEP_METERS = 300
PLANNING_GRID_STEP_METERS = 150
TARGET_DISTANCE_METERS = 250
MIN_CANDIDATE_DISTANCE_METERS = 350
MAX_CANDIDATES = 25
MAX_CANDIDATES_PER_NEIGHBORHOOD = 3
PLANNING_BUDGETS = (0, 5, 10, 15, 25)

RANDOM_STATE = 42
MONTE_CARLO_SAMPLES = 10_000
DIRICHLET_CONCENTRATION = 45
SPATIAL_K_NEIGHBORS = 5
SPATIAL_PERMUTATIONS = 999

DEFAULT_PRIORITY_WEIGHTS = {
    "vulnerability": 0.40,
    "capacity": 0.30,
    "accessibility": 0.20,
    "underserved": 0.10,
}

PRIORITY_SCENARIOS = {
    "default": DEFAULT_PRIORITY_WEIGHTS,
    "equity_focus": {
        "vulnerability": 0.55,
        "capacity": 0.20,
        "accessibility": 0.15,
        "underserved": 0.10,
    },
    "access_focus": {
        "vulnerability": 0.25,
        "capacity": 0.25,
        "accessibility": 0.35,
        "underserved": 0.15,
    },
}
