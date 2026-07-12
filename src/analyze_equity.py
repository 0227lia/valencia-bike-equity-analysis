"""Publication-ready figures and an evidence-led executive summary."""

from __future__ import annotations

import json

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd

from config import (
    CANDIDATE_LOCATIONS_PATH,
    COVERAGE_FRONTIER_PATH,
    EQUITY_SCORES_PATH,
    FIGURE_DIR,
    NEIGHBORHOODS_RAW_PATH,
    REPORT_DIR,
    SENSITIVITY_REPORT_PATH,
    SPATIAL_DIAGNOSTICS_PATH,
)

INK = "#172033"
MUTED = "#64748B"
GRID = "#DCE3EA"
TEAL = "#0F766E"
TEAL_LIGHT = "#99F6E4"
CORAL = "#E85D4A"
GOLD = "#D97706"
BLUE = "#2563EB"
VIOLET = "#7C3AED"


def _apply_style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.titleweight": "bold",
            "axes.titlecolor": INK,
            "axes.labelcolor": INK,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "axes.edgecolor": GRID,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
        }
    )


def _save(fig: plt.Figure, filename: str) -> None:
    fig.savefig(FIGURE_DIR / filename, dpi=190, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def _label_neighborhoods(data: pd.DataFrame) -> pd.Series:
    return data["neighborhood"].str.title() + " | " + data["district"].str.title()


def load_geojson() -> dict:
    return json.loads(NEIGHBORHOODS_RAW_PATH.read_text(encoding="utf-8"))


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, object]]:
    scores = pd.read_csv(EQUITY_SCORES_PATH)
    candidates = pd.read_csv(CANDIDATE_LOCATIONS_PATH)
    frontier = pd.read_csv(COVERAGE_FRONTIER_PATH)
    sensitivity = pd.read_csv(SENSITIVITY_REPORT_PATH)
    diagnostics = json.loads(SPATIAL_DIAGNOSTICS_PATH.read_text(encoding="utf-8"))
    return scores, candidates, frontier, sensitivity, diagnostics


def plot_polygon_outline(ax: plt.Axes, geometry: dict, *, color: str = "#CBD5E1") -> None:
    polygons = geometry["coordinates"] if geometry["type"] == "MultiPolygon" else [geometry["coordinates"]]
    for polygon in polygons:
        exterior = polygon[0]
        ax.plot(
            [point[0] for point in exterior],
            [point[1] for point in exterior],
            color=color,
            linewidth=0.35,
            zorder=1,
        )


def draw_priority_map(
    ax: plt.Axes,
    scores: pd.DataFrame,
    candidates: pd.DataFrame,
    *,
    include_legend: bool,
) -> None:
    geojson = load_geojson()
    score_by_codbar = scores.set_index("codbar")["priority_score"].to_dict()
    priority_values = scores["priority_score"]
    normalizer = mpl.colors.Normalize(vmin=priority_values.min(), vmax=priority_values.max())
    colormap = mpl.colormaps["YlOrRd"]

    for feature in geojson["features"]:
        codbar = int(feature["properties"]["codbar"])
        score = score_by_codbar[codbar]
        plot_polygon_outline(ax, feature["geometry"])
        centroid = feature["properties"]["geo_point_2d"]
        ax.scatter(
            centroid["lon"],
            centroid["lat"],
            s=24 + 240 * normalizer(score),
            color=colormap(normalizer(score)),
            alpha=0.9,
            edgecolor="white",
            linewidth=0.45,
            zorder=2,
        )

    selected = candidates.head(15)
    ax.scatter(
        selected["lon"],
        selected["lat"],
        s=70,
        marker="*",
        color=TEAL,
        edgecolor="white",
        linewidth=0.55,
        label="Área de revisión modelada (top 15)",
        zorder=3,
    )
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("Longitud")
    ax.set_ylabel("Latitud")
    ax.grid(False)
    if include_legend:
        colorbar = ax.figure.colorbar(
            mpl.cm.ScalarMappable(norm=normalizer, cmap=colormap),
            ax=ax,
            pad=0.02,
            shrink=0.74,
        )
        colorbar.set_label("Score de prioridad")
        ax.legend(loc="lower right", frameon=True, fontsize=8)


def plot_priority_map(scores: pd.DataFrame, candidates: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10.5, 8.6))
    draw_priority_map(ax, scores, candidates, include_legend=True)
    ax.set_title("Prioridad territorial y áreas de revisión modeladas", loc="left", pad=12)
    fig.text(
        0.125,
        0.015,
        "Puntos: centroides de barrio. Estrellas: cribado contrafactual, no propuestas de obra.",
        color=MUTED,
        fontsize=9,
    )
    _save(fig, "priority_map.png")


def draw_rank_intervals(ax: plt.Axes, scores: pd.DataFrame, *, limit: int = 15) -> None:
    ranking = scores.nsmallest(limit, "base_rank").sort_values("expected_rank", ascending=False).copy()
    labels = _label_neighborhoods(ranking)
    colors = mpl.colormaps["YlOrRd"](ranking["top_10_probability"].clip(0, 1))

    for position, (_, row) in enumerate(ranking.iterrows()):
        ax.hlines(position, row["rank_p05"], row["rank_p95"], color=GRID, linewidth=5, zorder=1)
        ax.scatter(
            row["expected_rank"],
            position,
            color=colors[position],
            edgecolor="white",
            linewidth=0.7,
            s=60,
            zorder=2,
        )
        ax.text(
            row["rank_p95"] + 0.45,
            position,
            f"{row['top_10_probability']:.0%}",
            va="center",
            color=MUTED,
            fontsize=8,
        )

    upper_bound = max(16, float(ranking["rank_p95"].max()) + 4)
    ax.set_yticks(range(len(ranking)), labels)
    ax.set_xlim(1, upper_bound)
    ax.set_xlabel("Rango simulado: 1 es mayor prioridad")
    ax.grid(axis="x", color=GRID, linewidth=0.7)
    ax.set_axisbelow(True)


def plot_rank_intervals(scores: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(12, 7.8))
    draw_rank_intervals(ax, scores)
    ax.set_title("Robustez del ranking bajo 10.000 escenarios de pesos", loc="left", pad=12)
    fig.text(
        0.125,
        0.01,
        (
            "Línea: intervalo percentil 5-95. Punto: rango esperado. "
            "Etiqueta: probabilidad de permanecer en top 10."
        ),
        color=MUTED,
        fontsize=9,
    )
    _save(fig, "robustness_rank_intervals.png")


def plot_top_priority_neighborhoods(scores: pd.DataFrame) -> None:
    ranking = scores.nsmallest(15, "base_rank").sort_values("priority_score").copy()
    labels = _label_neighborhoods(ranking)
    colors = mpl.colormaps["YlOrRd"](ranking["top_10_probability"].clip(0, 1))
    fig, ax = plt.subplots(figsize=(11, 7.3))
    bars = ax.barh(labels, ranking["priority_score"], color=colors, edgecolor="white", linewidth=0.6)
    for bar, probability in zip(bars, ranking["top_10_probability"], strict=True):
        ax.text(
            bar.get_width() + 0.009,
            bar.get_y() + bar.get_height() / 2,
            f"P(top 10) {probability:.0%}",
            va="center",
            color=MUTED,
            fontsize=8,
        )
    ax.set_xlim(0, min(1, float(ranking["priority_score"].max()) + 0.16))
    ax.set_xlabel("Score de prioridad base")
    ax.set_title("Barrios de mayor prioridad y estabilidad del top 10", loc="left", pad=12)
    ax.grid(axis="x", color=GRID, linewidth=0.7)
    ax.set_axisbelow(True)
    _save(fig, "top_priority_neighborhoods.png")


def draw_coverage_frontier(ax: plt.Axes, frontier: pd.DataFrame) -> None:
    budgets = frontier["budget"].to_numpy()
    weighted_reduction = 100 * frontier["weighted_gap_reduction_share"].to_numpy()
    coverage_reduction = 100 * frontier["underserved_reduction_share"].to_numpy()
    bars = ax.bar(budgets, weighted_reduction, width=2.3, color=TEAL, alpha=0.9, label="Déficit ponderado")
    ax.plot(
        budgets,
        coverage_reduction,
        color=CORAL,
        marker="o",
        linewidth=2.2,
        label="Puntos que pasan el umbral",
    )
    for bar, value in zip(bars, weighted_reduction, strict=True):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 2, f"{value:.0f}%", ha="center", fontsize=8)
    ax.set_ylim(0, min(105, max(80, float(weighted_reduction.max()) + 18)))
    ax.set_xlabel("Presupuesto de áreas de revisión")
    ax.set_ylabel("Reducción respecto al escenario base (%)")
    ax.set_xticks(budgets)
    ax.grid(axis="y", color=GRID, linewidth=0.7)
    ax.legend(frameon=False, loc="lower right", fontsize=8)
    ax.set_axisbelow(True)


def plot_coverage_frontier(frontier: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 5.5))
    draw_coverage_frontier(ax, frontier)
    ax.set_title("Frontera de impacto del plan contrafactual", loc="left", pad=12)
    fig.text(
        0.125,
        0.01,
        (
            "Simulación de distancias en línea recta sobre malla de 150 m; "
            "no estima demanda, capacidad ni viabilidad de calle."
        ),
        color=MUTED,
        fontsize=9,
    )
    _save(fig, "coverage_frontier.png")


def draw_spatial_quadrants(ax: plt.Axes, scores: pd.DataFrame, diagnostics: dict[str, object]) -> None:
    colors = {
        "high-high": CORAL,
        "high-low": GOLD,
        "low-high": BLUE,
        "low-low": "#94A3B8",
    }
    labels = {
        "high-high": "Alta prioridad rodeada de alta prioridad",
        "high-low": "Alta prioridad rodeada de menor prioridad",
        "low-high": "Menor prioridad rodeada de alta prioridad",
        "low-low": "Menor prioridad rodeada de menor prioridad",
    }
    for quadrant, frame in scores.groupby("spatial_quadrant", observed=True):
        ax.scatter(
            frame["priority_z_score"],
            frame["spatial_lag_z_score"],
            s=48,
            color=colors[quadrant],
            alpha=0.82,
            edgecolor="white",
            linewidth=0.45,
            label=labels[quadrant],
        )

    for _, row in scores.nlargest(5, "priority_score").iterrows():
        ax.annotate(
            row["neighborhood"].title(),
            (row["priority_z_score"], row["spatial_lag_z_score"]),
            xytext=(4, 4),
            textcoords="offset points",
            fontsize=7.5,
            color=INK,
        )
    ax.axhline(0, color=GRID, linewidth=1)
    ax.axvline(0, color=GRID, linewidth=1)
    ax.set_xlabel("Score de prioridad estandarizado")
    ax.set_ylabel("Lag espacial estandarizado (k=5)")
    ax.legend(frameon=False, fontsize=7.3, loc="best")
    ax.text(
        0.02,
        0.98,
        (
            f"Moran global I={diagnostics['morans_i']:.3f}\n"
            f"p permutación={diagnostics['permutation_p_value_two_sided']:.3f}"
        ),
        transform=ax.transAxes,
        va="top",
        ha="left",
        color=INK,
        fontsize=9,
        bbox={"facecolor": "white", "edgecolor": GRID, "pad": 5},
    )
    ax.grid(color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)


def plot_spatial_quadrants(scores: pd.DataFrame, diagnostics: dict[str, object]) -> None:
    fig, ax = plt.subplots(figsize=(10, 6.5))
    draw_spatial_quadrants(ax, scores, diagnostics)
    ax.set_title("Patrón espacial exploratorio de la prioridad", loc="left", pad=12)
    fig.text(
        0.125,
        0.01,
        "Los cuadrantes son descriptivos y no implican significación local individual.",
        color=MUTED,
        fontsize=9,
    )
    _save(fig, "spatial_quadrants.png")


def plot_vulnerability_vs_capacity(scores: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 6.2))
    scatter = ax.scatter(
        scores["spaces_per_km2"],
        scores["ind_global"],
        s=38 + 260 * scores["top_10_probability"],
        c=scores["priority_score"],
        cmap="YlOrRd",
        alpha=0.82,
        edgecolor="white",
        linewidth=0.5,
    )
    for _, row in scores.nlargest(6, "priority_score").iterrows():
        ax.annotate(
            row["neighborhood"].title(),
            (row["spaces_per_km2"], row["ind_global"]),
            xytext=(4, 4),
            textcoords="offset points",
            fontsize=8,
        )
    ax.invert_yaxis()
    ax.set_xlabel("Plazas declaradas por km²")
    ax.set_ylabel("Índice global de vulnerabilidad (menor = más vulnerable)")
    ax.set_title("Capacidad declarada, vulnerabilidad y prioridad", loc="left", pad=12)
    colorbar = fig.colorbar(scatter, ax=ax, pad=0.02)
    colorbar.set_label("Score de prioridad")
    ax.grid(color=GRID, linewidth=0.7)
    ax.set_axisbelow(True)
    _save(fig, "vulnerability_vs_capacity.png")


def plot_sensitivity_analysis(sensitivity: pd.DataFrame) -> None:
    labels = {
        "default": "Base",
        "equity_focus": "Más equidad",
        "access_focus": "Más accesibilidad",
    }
    display = sensitivity.copy()
    display["label"] = display["scenario"].map(labels)
    fig, ax = plt.subplots(figsize=(8.5, 5.4))
    bars = ax.bar(
        display["label"],
        display["rank_correlation_with_default"],
        color=[BLUE, VIOLET, GOLD],
        width=0.58,
    )
    for bar, overlap in zip(bars, display["top_10_overlap_count"], strict=True):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.02,
            f"{int(overlap)}/10 en top 10",
            ha="center",
            color=INK,
            fontsize=9,
        )
    ax.set_ylim(0, 1.12)
    ax.set_ylabel("Correlación de rangos frente al escenario base")
    ax.set_title("Sensibilidad a tres políticas explícitas de ponderación", loc="left", pad=12)
    ax.grid(axis="y", color=GRID, linewidth=0.7)
    ax.set_axisbelow(True)
    _save(fig, "ranking_sensitivity.png")


def plot_scorecard(scores: pd.DataFrame) -> None:
    top = scores.nsmallest(10, "base_rank").copy()
    table = pd.DataFrame(
        {
            "Barrio": top["neighborhood"].str.title(),
            "Rango base": top["base_rank"].astype(int),
            "Rango esperado": top["expected_rank"].map(lambda value: f"{value:.1f}"),
            "Intervalo 5-95": top.apply(
                lambda row: f"{row['rank_p05']:.0f}-{row['rank_p95']:.0f}", axis=1
            ),
            "P(top 10)": top["top_10_probability"].map(lambda value: f"{value:.0%}"),
            "Cobertura insuf.": top["underserved_share"].map(lambda value: f"{value:.0%}"),
        }
    )
    fig, ax = plt.subplots(figsize=(12, 4.9))
    ax.axis("off")
    table_plot = ax.table(
        cellText=table.values,
        colLabels=table.columns,
        loc="center",
        cellLoc="left",
        colLoc="left",
        colWidths=[0.24, 0.13, 0.15, 0.17, 0.14, 0.17],
    )
    table_plot.auto_set_font_size(False)
    table_plot.set_fontsize(9)
    table_plot.scale(1, 1.55)
    for (row, _column), cell in table_plot.get_celld().items():
        cell.set_edgecolor("white")
        if row == 0:
            cell.set_facecolor(INK)
            cell.set_text_props(color="white", weight="bold")
        elif row % 2:
            cell.set_facecolor("#F8FAFC")
        else:
            cell.set_facecolor("#EAF4F2")
    ax.set_title("Scorecard de barrios prioritarios", loc="left", color=INK, pad=14, weight="bold")
    _save(fig, "equity_scorecard.png")


def plot_decision_dashboard(
    scores: pd.DataFrame,
    candidates: pd.DataFrame,
    frontier: pd.DataFrame,
    diagnostics: dict[str, object],
) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(15, 11))
    draw_priority_map(axes[0, 0], scores, candidates, include_legend=False)
    axes[0, 0].set_title("Prioridad territorial y revisión", loc="left")
    draw_rank_intervals(axes[0, 1], scores, limit=10)
    axes[0, 1].set_title("Robustez del top 10", loc="left")
    draw_coverage_frontier(axes[1, 0], frontier)
    axes[1, 0].set_title("Frontera contrafactual", loc="left")
    draw_spatial_quadrants(axes[1, 1], scores, diagnostics)
    axes[1, 1].set_title("Diagnóstico espacial", loc="left")
    fig.suptitle(
        "Valencia Bike Equity | panel de decisión exploratorio",
        x=0.075,
        ha="left",
        fontsize=17,
        weight="bold",
    )
    fig.text(
        0.075,
        0.015,
        (
            "Resultados reproducibles con datos abiertos municipales. El análisis orienta revisión; "
            "no determina inversión ni viabilidad física."
        ),
        color=MUTED,
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.03, 1, 0.96))
    _save(fig, "equity_decision_dashboard.png")


def write_executive_summary(
    scores: pd.DataFrame,
    candidates: pd.DataFrame,
    frontier: pd.DataFrame,
    sensitivity: pd.DataFrame,
    diagnostics: dict[str, object],
) -> None:
    budget_25 = frontier.loc[frontier["budget"] == frontier["budget"].max()].iloc[0]
    top = scores.nsmallest(10, "base_rank")
    robust_top_10 = int((scores["top_10_probability"] >= 0.8).sum())
    top_candidates = candidates.head(10)

    lines = [
        "# Resumen ejecutivo",
        "",
        (
            "Este proyecto realiza un cribado geoespacial reproducible para identificar barrios y zonas de "
            "Valencia que merecen una revisión más detallada de aparcamiento de bicicletas. Combina "
            "vulnerabilidad urbana, capacidad declarada y distancia al aparcamiento más cercano."
        ),
        "",
        "## Qué aporta el análisis",
        "",
        "- **70 barrios** y **4.316 puntos de aparcamiento** procesados desde snapshots públicos.",
        "- Malla de diagnóstico de 300 m y malla de simulación de 150 m.",
        (
            f"- **10.000 simulaciones de pesos**: {robust_top_10} barrios tienen al menos un 80% de "
            "probabilidad de mantenerse en el top 10."
        ),
        (
            f"- Moran global I={diagnostics['morans_i']:.3f}; prueba por permutación bilateral "
            f"p={diagnostics['permutation_p_value_two_sided']:.3f} con k={diagnostics['knn_neighbors']}."
        ),
        (
            f"- En el escenario de {int(budget_25['budget'])} áreas de revisión, el modelo reduce el "
            f"déficit de distancia ponderado un {budget_25['weighted_gap_reduction_share']:.1%} y "
            f"lleva {int(budget_25['underserved_points_covered'])} puntos de malla por debajo del umbral."
        ),
        "",
        "## Ranking con incertidumbre",
        "",
    ]

    for _, row in top.iterrows():
        lines.append(
            f"- **{row['neighborhood'].title()}** ({row['district'].title()}): rango base "
            f"{int(row['base_rank'])}, rango esperado {row['expected_rank']:.1f}, intervalo 5-95 "
            f"{row['rank_p05']:.0f}-{row['rank_p95']:.0f}, P(top 10)={row['top_10_probability']:.1%}."
        )

    lines.extend(["", "## Sensibilidad a políticas explícitas", ""])
    for _, row in sensitivity.iterrows():
        lines.append(
            f"- `{row['scenario']}`: correlación de rangos={row['rank_correlation_with_default']:.3f}; "
            f"solapamiento top 10={int(row['top_10_overlap_count'])}/10."
        )

    lines.extend(["", "## Áreas de revisión modeladas", ""])
    for _, row in top_candidates.iterrows():
        lines.append(
            f"- Puesto {int(row['candidate_rank'])}: **{row['neighborhood'].title()}** "
            f"({row['district'].title()}), distancia actual={row['nearest_bike_parking_m']:.0f} m, "
            f"ganancia marginal ponderada={row['marginal_weighted_gap_reduction_m']:.0f} m."
        )

    lines.extend(
        [
            "",
            "## Interpretación y límites",
            "",
            (
                "Las áreas de revisión no son propuestas de obra. El modelo usa distancia en línea recta, "
                "no rutas reales, demanda, ocupación, capacidad futura, coste, propiedad, red viaria ni "
                "restricciones urbanísticas. Moran es un diagnóstico global exploratorio; los cuadrantes "
                "locales no son pruebas de significación. Cualquier intervención requeriría validación de "
                "calle, participación, datos de demanda y una evaluación técnica municipal."
            ),
        ]
    )
    (REPORT_DIR / "executive_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    _apply_style()
    scores, candidates, frontier, sensitivity, diagnostics = load_inputs()
    plot_priority_map(scores, candidates)
    plot_rank_intervals(scores)
    plot_top_priority_neighborhoods(scores)
    plot_coverage_frontier(frontier)
    plot_spatial_quadrants(scores, diagnostics)
    plot_vulnerability_vs_capacity(scores)
    plot_sensitivity_analysis(sensitivity)
    plot_scorecard(scores)
    plot_decision_dashboard(scores, candidates, frontier, diagnostics)
    write_executive_summary(scores, candidates, frontier, sensitivity, diagnostics)
    print(f"Report saved to {REPORT_DIR}")


if __name__ == "__main__":
    main()
