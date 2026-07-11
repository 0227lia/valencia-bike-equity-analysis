import json

import matplotlib.pyplot as plt
import pandas as pd

from config import (
    BIKE_PARKING_ENRICHED_PATH,
    CANDIDATE_LOCATIONS_PATH,
    EQUITY_SCORES_PATH,
    FIGURE_DIR,
    NEIGHBORHOODS_RAW_PATH,
    REPORT_DIR,
    SENSITIVITY_REPORT_PATH,
)


def load_geojson() -> dict:
    return json.loads(NEIGHBORHOODS_RAW_PATH.read_text(encoding="utf-8"))


def plot_polygon_outline(ax, geometry: dict, color: str = "#9ca3af", linewidth: float = 0.5) -> None:
    geometry_type = geometry["type"]
    polygons = geometry["coordinates"] if geometry_type == "MultiPolygon" else [geometry["coordinates"]]

    for polygon in polygons:
        exterior = polygon[0]
        lons = [point[0] for point in exterior]
        lats = [point[1] for point in exterior]
        ax.plot(lons, lats, color=color, linewidth=linewidth)


def plot_priority_map() -> None:
    scores = pd.read_csv(EQUITY_SCORES_PATH)
    candidates = pd.read_csv(CANDIDATE_LOCATIONS_PATH)
    bike_parking = pd.read_csv(BIKE_PARKING_ENRICHED_PATH).dropna(subset=["codbar"])
    geojson = load_geojson()

    score_by_codbar = scores.set_index("codbar")["priority_score"].to_dict()
    max_score = scores["priority_score"].max()

    fig, ax = plt.subplots(figsize=(10, 10))
    for feature in geojson["features"]:
        codbar = int(feature["properties"]["codbar"])
        score = score_by_codbar.get(codbar, 0)
        alpha = 0.15 + 0.75 * (score / max_score)
        plot_polygon_outline(ax, feature["geometry"], color="#4b5563", linewidth=0.4)
        centroid = feature["properties"]["geo_point_2d"]
        ax.scatter(
            centroid["lon"],
            centroid["lat"],
            s=50 + 350 * score,
            color="#ef4444",
            alpha=alpha,
            edgecolor="white",
            linewidth=0.4,
        )

    ax.scatter(
        bike_parking["lon"],
        bike_parking["lat"],
        s=4,
        color="#2563eb",
        alpha=0.25,
        label="Aparcamiento existente",
    )
    ax.scatter(
        candidates["lon"],
        candidates["lat"],
        s=85,
        marker="*",
        color="#f59e0b",
        edgecolor="#111827",
        linewidth=0.5,
        label="Ubicación candidata",
    )

    ax.set_title("Prioridad territorial de aparcamientos de bicicleta en Valencia")
    ax.set_xlabel("Longitud")
    ax.set_ylabel("Latitud")
    ax.legend(loc="lower right")
    ax.set_aspect("equal", adjustable="box")
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "priority_map.png", dpi=180)
    plt.close()


def plot_top_priority_neighborhoods() -> None:
    scores = pd.read_csv(EQUITY_SCORES_PATH).head(15).sort_values("priority_score")
    labels = scores["neighborhood"] + " (" + scores["district"] + ")"

    plt.figure(figsize=(10, 7))
    plt.barh(labels, scores["priority_score"], color="#ef4444")
    plt.title("Barrios con mayor prioridad de revisión")
    plt.xlabel("Score de prioridad")
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "top_priority_neighborhoods.png", dpi=180)
    plt.close()


def plot_vulnerability_vs_capacity() -> None:
    scores = pd.read_csv(EQUITY_SCORES_PATH)

    plt.figure(figsize=(9, 6))
    scatter = plt.scatter(
        scores["spaces_per_km2"],
        scores["ind_global"],
        s=70 + 500 * scores["priority_score"],
        c=scores["priority_score"],
        cmap="Reds",
        alpha=0.75,
        edgecolor="#111827",
        linewidth=0.3,
    )
    plt.gca().invert_yaxis()
    plt.title("Vulnerabilidad y capacidad de aparcamiento")
    plt.xlabel("Plazas de bicicleta por km²")
    plt.ylabel("Índice global; un valor menor indica más vulnerabilidad")
    plt.colorbar(scatter, label="Score de prioridad")
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "vulnerability_vs_capacity.png", dpi=180)
    plt.close()


def plot_sensitivity_analysis() -> None:
    sensitivity = pd.read_csv(SENSITIVITY_REPORT_PATH)
    label_by_scenario = {
        "default": "Base",
        "equity_focus": "Más equidad",
        "access_focus": "Más accesibilidad",
    }
    labels = sensitivity["scenario"].map(label_by_scenario)

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(
        labels,
        sensitivity["rank_correlation_with_default"],
        color=["#2563eb", "#ef4444", "#f59e0b"],
    )
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("Correlación de rangos con el escenario base")
    ax.set_title("Sensibilidad del ranking a los pesos del score")
    for bar, overlap in zip(bars, sensitivity["top_10_overlap_count"], strict=True):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.02,
            f"{int(overlap)}/10 en top 10",
            ha="center",
            fontsize=9,
        )
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "ranking_sensitivity.png", dpi=180)
    plt.close()


def write_executive_summary() -> None:
    scores = pd.read_csv(EQUITY_SCORES_PATH)
    candidates = pd.read_csv(CANDIDATE_LOCATIONS_PATH)
    sensitivity = pd.read_csv(SENSITIVITY_REPORT_PATH)

    top = scores.head(10)
    top_candidates = candidates.head(10)

    lines = [
        "# Resumen ejecutivo",
        "",
        (
            "Este análisis prioriza barrios de Valencia para ampliar la red de aparcamientos de bicicleta. "
            "El criterio combina vulnerabilidad urbana, capacidad existente y distancia estimada hasta el "
            "aparcamiento más cercano."
        ),
        "",
        "## Métricas principales",
        "",
        f"- Barrios analizados: {len(scores)}",
        f"- Ubicaciones candidatas propuestas: {len(candidates)}",
        f"- Barrio con mayor prioridad: {scores.iloc[0]['neighborhood']} ({scores.iloc[0]['district']})",
        (
            "- Mediana de distancia p90 al aparcamiento más cercano: "
            f"{scores['p90_nearest_bike_parking_m'].median():.0f} metros"
        ),
        "",
        "## Barrios con mayor prioridad",
        "",
    ]

    for _, row in top.iterrows():
        lines.append(
            f"- {row['neighborhood']} ({row['district']}): prioridad={row['priority_score']:.3f}, "
            f"plazas/km2={row['spaces_per_km2']:.1f}, cobertura insuficiente={row['underserved_share']:.1%}"
        )

    lines.extend(
        [
            "",
            "## Sensibilidad del ranking",
            "",
            "Se comparó el escenario base con alternativas que dan más peso a equidad o accesibilidad.",
            (
                "La correlación mide estabilidad global y el solapamiento indica cuántos barrios "
                "permanecen en el top 10."
            ),
            "",
        ]
    )

    for _, row in sensitivity.iterrows():
        lines.append(
            f"- {row['scenario']}: correlación={row['rank_correlation_with_default']:.3f}, "
            f"coincidencia top 10={int(row['top_10_overlap_count'])}/10"
        )

    lines.extend(["", "## Ubicaciones candidatas principales", ""])

    for _, row in top_candidates.iterrows():
        lines.append(
            f"- Puesto {int(row['candidate_rank'])}: {row['neighborhood']} ({row['district']}), "
            f"lat={row['lat']:.6f}, lon={row['lon']:.6f}, "
            f"aparcamiento existente más cercano={row['nearest_bike_parking_m']:.0f}m"
        )

    lines.extend(
        [
            "",
            "## Interpretación",
            "",
            (
                "El score de prioridad debe leerse como una señal de apoyo al análisis, no como una "
                "decisión automática. El siguiente paso sería validar las ubicaciones candidatas con "
                "información de calle, demanda ciclista, disponibilidad de espacio y restricciones "
                "urbanísticas."
            ),
        ]
    )

    (REPORT_DIR / "executive_summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    plot_priority_map()
    plot_top_priority_neighborhoods()
    plot_vulnerability_vs_capacity()
    plot_sensitivity_analysis()
    write_executive_summary()
    print(f"Report saved to {REPORT_DIR}")


if __name__ == "__main__":
    main()
