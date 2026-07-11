# Diccionario de datos

## `neighborhood_equity_scores.csv`

| Campo | Descripción |
|---|---|
| `codbar` | Identificador municipal del barrio. |
| `neighborhood`, `district` | Nombre del barrio y distrito. |
| `bike_parking_points` | Número de ubicaciones de aparcamiento asignadas. |
| `bike_parking_spaces` | Suma de plazas declaradas. |
| `spaces_per_km2` | Plazas declaradas divididas por superficie. |
| `median_nearest_bike_parking_m` | Mediana de distancia desde la malla. |
| `p90_nearest_bike_parking_m` | Percentil 90 de distancia desde la malla. |
| `underserved_share` | Proporción de puntos a más de 250 metros. |
| `vulnerability_pressure` | Vulnerabilidad normalizada e invertida. |
| `capacity_gap` | Déficit normalizado de plazas por km². |
| `accessibility_gap` | Distancia p90 normalizada. |
| `underserved_gap` | Cobertura insuficiente normalizada. |
| `priority_score` | Combinación ponderada del escenario base. |

## `candidate_locations.csv`

| Campo | Descripción |
|---|---|
| `candidate_rank` | Orden según el score candidato. |
| `codbar`, `neighborhood`, `district` | Área municipal asociada. |
| `lat`, `lon` | Coordenadas del punto de malla. |
| `nearest_bike_parking_m` | Distancia en línea recta al punto existente más cercano. |
| `priority_score` | Prioridad del barrio. |
| `candidate_score` | Combinación de prioridad y déficit de distancia. |

## `sensitivity_analysis.csv`

| Campo | Descripción |
|---|---|
| `scenario` | Conjunto de pesos evaluado. |
| `rank_correlation_with_default` | Correlación del ranking con el escenario base. |
| `top_10_overlap_count` | Barrios que coinciden en ambos top 10. |
| `weight_*` | Peso usado por cada componente. |
