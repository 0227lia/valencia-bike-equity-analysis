# Diccionario de datos

## `data/processed/neighborhood_equity_scores.csv`

| Campo | Descripción |
|---|---|
| `codbar`, `neighborhood`, `district` | Identificador y nombres municipales del barrio. |
| `ind_*`, `vul_global` | Indicadores de vulnerabilidad originales. |
| `area_m2`, `area_km2`, `centroid_*` | Superficie y centroide publicados o derivados. |
| `bike_parking_points`, `bike_parking_spaces` | Recuento de puntos y suma de plazas declaradas dentro del barrio. |
| `spaces_per_km2`, `points_per_km2` | Densidades de infraestructura por superficie. |
| `grid_points`, `underserved_share` | Malla de 300 m y proporción por encima de 250 m. |
| `median_nearest_bike_parking_m`, `p90_nearest_bike_parking_m` | Resúmenes de distancia geodésica a la infraestructura existente. |
| `vulnerability_pressure`, `capacity_gap`, `accessibility_gap`, `underserved_gap` | Componentes normalizados entre 0 y 1. |
| `priority_score`, `base_rank` | Score y rango del escenario base. |
| `expected_priority_score`, `priority_score_p05`, `priority_score_p95` | Distribución de score bajo muestreo de pesos. |
| `expected_rank`, `rank_p05`, `rank_p50`, `rank_p95`, `rank_interval_width` | Distribución del rango bajo muestreo de pesos. |
| `top_1_probability`, `top_5_probability`, `top_10_probability` | Frecuencia empírica de pertenecer a cada top bajo 10.000 muestras. |
| `priority_z_score`, `spatial_lag_z_score`, `spatial_quadrant` | Diagnóstico espacial descriptivo k-NN. |

## `data/processed/accessibility_grid.csv` y `planning_grid.csv`

| Campo | Descripción |
|---|---|
| `codbar`, `neighborhood`, `district` | Barrio asociado. |
| `grid_point`, `lat`, `lon` | Identificador y coordenada del centro de celda interior. |
| `nearest_bike_parking_m` | Distancia geodésica al punto existente más cercano. |
| `is_underserved` | Verdadero si supera 250 m. |

`accessibility_grid.csv` usa una separación aproximada de 300 m; `planning_grid.csv` usa 150 m.

## `data/processed/weight_robustness.csv`

Versión compacta de las columnas de incertidumbre de ranking, separada para consumo analítico y auditoría del modelo de pesos.

## `data/processed/neighborhood_spatial_clusters.csv`

Incluye score, z-score, lag espacial estandarizado, cuadrante descriptivo y número de vecinos usados. No contiene p-values locales.

## `data/processed/candidate_locations.csv`

| Campo | Descripción |
|---|---|
| `candidate_rank` | Orden greedy dentro de la cartera contrafactual. |
| `candidate_type` | Siempre `modeled_review_area`; no es una propuesta de obra. |
| `planning_grid_point`, `lat`, `lon` | Punto de malla de 150 m usado como ubicación de cribado. |
| `nearest_bike_parking_m` | Déficit de distancia antes de añadir el candidato. |
| `priority_score`, `top_10_probability`, `expected_rank` | Contexto de prioridad y robustez del barrio. |
| `marginal_newly_served_grid_points` | Puntos que pasan por primera vez por debajo de 250 m en ese paso. |
| `marginal_weighted_gap_reduction_m` | Reducción marginal de déficit de distancia ponderado. |
| `cumulative_*` | Impacto acumulado hasta esa posición en la cartera. |

## `reports/coverage_frontier.csv`

| Campo | Descripción |
|---|---|
| `budget`, `selected_candidates` | Tamaño solicitado y tamaño realmente seleccionado de la cartera. |
| `candidate_pool_size` | Puntos de malla elegibles antes de aplicar restricciones. |
| `baseline_*` | Estado de referencia sin áreas añadidas. |
| `underserved_points_*` | Recuento de puntos sobre el umbral antes/después del escenario. |
| `weighted_gap_reduction_*` | Reducción de déficit de distancia ponderado en metros y proporción. |

## JSON de auditoría

- `reports/robustness_summary.json`: parámetros y estadísticas de pesos Dirichlet.
- `reports/spatial_diagnostics.json`: Moran global, distribución de permutaciones y parámetros k-NN.
