"""Interactive decision dashboard for the Valencia bike-parking equity analysis."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent
PROCESSED_DIR = ROOT / "data" / "processed"
REPORT_DIR = ROOT / "reports"

COMPONENTS = {
    "Vulnerabilidad": "vulnerability_pressure",
    "Déficit de plazas": "capacity_gap",
    "Accesibilidad": "accessibility_gap",
    "Cobertura insuficiente": "underserved_gap",
}
DEFAULT_WEIGHT_PERCENTAGES = {
    "Vulnerabilidad": 40,
    "Déficit de plazas": 30,
    "Accesibilidad": 20,
    "Cobertura insuficiente": 10,
}
COLORS = {
    "ink": "#172033",
    "muted": "#64748B",
    "teal": "#0F766E",
    "coral": "#E85D4A",
    "gold": "#D97706",
    "blue": "#2563EB",
    "grid": "#DCE3EA",
}


def _path(filename: str, directory: Path = PROCESSED_DIR) -> Path:
    return directory / filename


@st.cache_data(show_spinner=False)
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, object]]:
    scores = pd.read_csv(_path("neighborhood_equity_scores.csv"))
    candidates = pd.read_csv(_path("candidate_locations.csv"))
    frontier = pd.read_csv(_path("coverage_frontier.csv", REPORT_DIR))
    diagnostics = json.loads(_path("spatial_diagnostics.json", REPORT_DIR).read_text(encoding="utf-8"))
    return scores, candidates, frontier, diagnostics


def apply_weights(scores: pd.DataFrame, percentages: dict[str, int]) -> tuple[pd.DataFrame, dict[str, float]]:
    total = sum(percentages.values())
    if total <= 0:
        raise ValueError("La suma de los pesos debe ser mayor que cero")

    weights = {name: value / total for name, value in percentages.items()}
    result = scores.copy()
    result["scenario_priority_score"] = sum(
        weights[label] * result[column] for label, column in COMPONENTS.items()
    )
    result["scenario_rank"] = result["scenario_priority_score"].rank(
        ascending=False,
        method="first",
    ).astype(int)
    return result.sort_values("scenario_rank"), weights


def base_layout(title: str | None = None) -> dict[str, object]:
    layout: dict[str, object] = {
        "paper_bgcolor": "white",
        "plot_bgcolor": "white",
        "font": {"family": "Arial, sans-serif", "color": COLORS["ink"]},
        "margin": {"l": 12, "r": 12, "t": 46 if title else 18, "b": 12},
        "legend": {"orientation": "h", "y": -0.16},
        "xaxis": {"gridcolor": COLORS["grid"], "zerolinecolor": COLORS["grid"]},
        "yaxis": {"gridcolor": COLORS["grid"], "zerolinecolor": COLORS["grid"]},
    }
    if title:
        layout["title"] = {"text": title, "font": {"size": 18, "color": COLORS["ink"]}}
    return layout


def priority_map(scores: pd.DataFrame, candidates: pd.DataFrame, budget: int) -> go.Figure:
    selected = candidates.loc[candidates["candidate_rank"] <= budget]
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=scores["centroid_lon"],
            y=scores["centroid_lat"],
            mode="markers",
            name="Barrios",
            customdata=np.column_stack(
                [
                    scores["neighborhood"],
                    scores["district"],
                    scores["scenario_rank"],
                    scores["scenario_priority_score"],
                    scores["top_10_probability"],
                ]
            ),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>%{customdata[1]}<br>"
                "Rango actual: %{customdata[2]}<br>Score: %{customdata[3]:.3f}<br>"
                "P(top 10) base: %{customdata[4]:.0%}<extra></extra>"
            ),
            marker={
                "size": 10 + 24 * scores["scenario_priority_score"],
                "color": scores["scenario_priority_score"],
                "colorscale": "YlOrRd",
                "showscale": True,
                "colorbar": {"title": "Score"},
                "line": {"width": 0.7, "color": "white"},
                "opacity": 0.9,
            },
        )
    )
    if budget:
        fig.add_trace(
            go.Scatter(
                x=selected["lon"],
                y=selected["lat"],
                mode="markers",
                name="Áreas de revisión",
                customdata=np.column_stack(
                    [
                        selected["candidate_rank"],
                        selected["neighborhood"],
                        selected["nearest_bike_parking_m"],
                        selected["marginal_weighted_gap_reduction_m"],
                    ]
                ),
                hovertemplate=(
                    "<b>Área %{customdata[0]}</b><br>%{customdata[1]}<br>"
                    "Distancia actual: %{customdata[2]:.0f} m<br>"
                    "Ganancia ponderada: %{customdata[3]:.0f} m<extra></extra>"
                ),
                marker={
                    "size": 13,
                    "symbol": "star",
                    "color": COLORS["teal"],
                    "line": {"width": 1, "color": "white"},
                },
            )
        )
    fig.update_layout(**base_layout())
    fig.update_xaxes(title="Longitud", showgrid=False)
    fig.update_yaxes(title="Latitud", showgrid=False, scaleanchor="x", scaleratio=1)
    return fig


def weight_chart(weights: dict[str, float]) -> go.Figure:
    labels = list(weights)
    values = [100 * weights[label] for label in labels]
    fig = go.Figure(
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker_color=[COLORS["teal"], COLORS["blue"], COLORS["gold"], COLORS["coral"]],
            text=[f"{value:.1f}%" for value in values],
            textposition="outside",
        )
    )
    fig.update_layout(**base_layout())
    fig.update_xaxes(range=[0, max(values) + 12], title="Peso normalizado (%)")
    fig.update_yaxes(autorange="reversed", showgrid=False)
    return fig


def rank_comparison_chart(scores: pd.DataFrame) -> go.Figure:
    display = scores.nsmallest(15, "scenario_rank").sort_values("scenario_rank", ascending=False)
    fig = go.Figure()
    for _, row in display.iterrows():
        fig.add_shape(
            type="line",
            x0=row["base_rank"],
            x1=row["scenario_rank"],
            y0=row["neighborhood"],
            y1=row["neighborhood"],
            line={"color": COLORS["grid"], "width": 4},
        )
    fig.add_trace(
        go.Scatter(
            x=display["base_rank"],
            y=display["neighborhood"],
            mode="markers",
            name="Base",
            marker={"size": 9, "color": COLORS["muted"]},
            hovertemplate="%{y}<br>Rango base: %{x}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=display["scenario_rank"],
            y=display["neighborhood"],
            mode="markers",
            name="Escenario actual",
            marker={"size": 10, "color": COLORS["coral"]},
            hovertemplate="%{y}<br>Rango actual: %{x}<extra></extra>",
        )
    )
    fig.update_layout(**base_layout())
    fig.update_xaxes(title="Rango: 1 es mayor prioridad", autorange="reversed")
    fig.update_yaxes(title=None)
    return fig


def coverage_chart(frontier: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=frontier["budget"],
            y=100 * frontier["weighted_gap_reduction_share"],
            name="Déficit ponderado",
            marker_color=COLORS["teal"],
            hovertemplate="%{x} áreas<br>%{y:.1f}%<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=frontier["budget"],
            y=100 * frontier["underserved_reduction_share"],
            name="Puntos bajo umbral",
            mode="lines+markers",
            line={"color": COLORS["coral"], "width": 3},
            marker={"size": 8},
            hovertemplate="%{x} áreas<br>%{y:.1f}%<extra></extra>",
        )
    )
    fig.update_layout(**base_layout())
    fig.update_xaxes(title="Áreas de revisión modeladas", tickmode="array", tickvals=frontier["budget"])
    fig.update_yaxes(title="Reducción frente a base (%)", range=[0, 100])
    return fig


def spatial_chart(scores: pd.DataFrame) -> go.Figure:
    label_map = {
        "high-high": "Alta / alta",
        "high-low": "Alta / baja",
        "low-high": "Baja / alta",
        "low-low": "Baja / baja",
    }
    color_map = {
        "Alta / alta": COLORS["coral"],
        "Alta / baja": COLORS["gold"],
        "Baja / alta": COLORS["blue"],
        "Baja / baja": "#94A3B8",
    }
    display = scores.copy()
    display["quadrant_label"] = display["spatial_quadrant"].map(label_map)
    fig = px.scatter(
        display,
        x="priority_z_score",
        y="spatial_lag_z_score",
        color="quadrant_label",
        color_discrete_map=color_map,
        hover_name="neighborhood",
        hover_data={"district": True, "priority_score": ":.3f", "quadrant_label": False},
    )
    fig.add_hline(y=0, line_color=COLORS["grid"])
    fig.add_vline(x=0, line_color=COLORS["grid"])
    fig.update_traces(marker={"size": 10, "line": {"color": "white", "width": 0.6}})
    fig.update_layout(**base_layout())
    fig.update_xaxes(title="Prioridad estandarizada")
    fig.update_yaxes(title="Lag espacial estandarizado (k=5)")
    return fig


def dataframe_style(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.rename(
        columns={
            "neighborhood": "Barrio",
            "district": "Distrito",
            "scenario_rank": "Rango actual",
            "scenario_priority_score": "Score actual",
            "base_rank": "Rango base",
            "expected_rank": "Rango esperado",
            "top_10_probability": "P(top 10) base",
            "underserved_share": "Cobertura insuficiente",
        }
    )


def main() -> None:
    st.set_page_config(
        page_title="Valencia Bike Equity",
        page_icon=":material/directions_bike:",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        """
        <style>
        .block-container {max-width: 1480px; padding-top: 1.25rem; padding-bottom: 2rem;}
        h1, h2, h3 {letter-spacing: 0 !important; color: #172033;}
        [data-testid="stMetric"] {
            background: #F8FAFC; border: 1px solid #DCE3EA; padding: 0.7rem; border-radius: 6px;
        }
        [data-testid="stSidebar"] {background: #F8FAFC;}
        </style>
        """,
        unsafe_allow_html=True,
    )

    required = [
        _path("neighborhood_equity_scores.csv"),
        _path("candidate_locations.csv"),
        _path("coverage_frontier.csv", REPORT_DIR),
        _path("spatial_diagnostics.json", REPORT_DIR),
    ]
    if any(not path.exists() for path in required):
        st.error("No se encuentran las salidas del pipeline. Ejecuta `python src/run_pipeline.py`.")
        st.stop()

    scores, candidates, frontier, diagnostics = load_data()

    with st.sidebar:
        st.header("Pesos de prioridad")
        percentages = {
            label: st.slider(
                label,
                min_value=0,
                max_value=100,
                value=DEFAULT_WEIGHT_PERCENTAGES[label],
                step=1,
            )
            for label in COMPONENTS
        }
        st.divider()
        st.caption(f"Suma introducida: {sum(percentages.values())}% | se normaliza al 100%")
        st.caption("La cartera contrafactual mostrada corresponde al escenario base reproducible.")

    try:
        scenario_scores, normalized_weights = apply_weights(scores, percentages)
    except ValueError:
        st.error("Introduce al menos un peso mayor que cero.")
        st.stop()

    st.title("Valencia Bike Equity")
    st.caption("Panel exploratorio de equidad territorial para aparcamiento de bicicletas")
    tabs = st.tabs(["Panorama", "Pesos", "Plan", "Espacio", "Datos"])

    with tabs[0]:
        leader = scenario_scores.iloc[0]
        budget_25 = frontier.loc[frontier["budget"] == frontier["budget"].max()].iloc[0]
        first_row = st.columns(4)
        first_row[0].metric("Mayor prioridad", leader["neighborhood"].title())
        first_row[1].metric("Score actual", f"{leader['scenario_priority_score']:.3f}")
        first_row[2].metric("Robustez top 10", f"{leader['top_10_probability']:.0%}")
        first_row[3].metric(
            "Reducción de déficit (25)",
            f"{budget_25['weighted_gap_reduction_share']:.1%}",
        )
        left, right = st.columns([1.45, 1])
        with left:
            st.plotly_chart(
                priority_map(scenario_scores, candidates, budget=10),
                use_container_width=True,
                key="overview_priority_map",
            )
        with right:
            top = scenario_scores.nsmallest(12, "scenario_rank")[
                [
                    "neighborhood",
                    "district",
                    "scenario_rank",
                    "scenario_priority_score",
                    "top_10_probability",
                    "underserved_share",
                ]
            ]
            st.dataframe(
                dataframe_style(top),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Score actual": st.column_config.NumberColumn(format="%.3f"),
                    "P(top 10) base": st.column_config.ProgressColumn(
                        format="%.0f%%",
                        min_value=0,
                        max_value=1,
                    ),
                    "Cobertura insuficiente": st.column_config.ProgressColumn(
                        format="%.0f%%", min_value=0, max_value=1
                    ),
                },
            )

    with tabs[1]:
        left, right = st.columns([0.65, 1.35])
        with left:
            st.plotly_chart(
                weight_chart(normalized_weights),
                use_container_width=True,
                key="weight_distribution",
            )
        with right:
            st.plotly_chart(
                rank_comparison_chart(scenario_scores),
                use_container_width=True,
                key="rank_comparison",
            )
        movements = scenario_scores.assign(
            change_vs_base=scenario_scores["base_rank"] - scenario_scores["scenario_rank"]
        ).sort_values("scenario_rank")[
            [
                "neighborhood",
                "district",
                "scenario_rank",
                "base_rank",
                "change_vs_base",
                "top_10_probability",
            ]
        ].head(20)
        st.dataframe(
            dataframe_style(movements).rename(columns={"change_vs_base": "Cambio vs. base"}),
            use_container_width=True,
            hide_index=True,
            column_config={"P(top 10) base": st.column_config.NumberColumn(format="%.0f%%")},
        )

    with tabs[2]:
        budget = st.select_slider(
            "Cartera de áreas de revisión",
            options=frontier["budget"].tolist(),
            value=10,
        )
        selected = candidates.loc[candidates["candidate_rank"] <= budget]
        state = frontier.loc[frontier["budget"] == budget].iloc[0]
        metrics = st.columns(4)
        metrics[0].metric("Áreas seleccionadas", int(state["selected_candidates"]))
        metrics[1].metric("Puntos bajo umbral", int(state["underserved_points_covered"]))
        metrics[2].metric("Reducción bajo umbral", f"{state['underserved_reduction_share']:.1%}")
        metrics[3].metric("Reducción ponderada", f"{state['weighted_gap_reduction_share']:.1%}")
        left, right = st.columns([1, 1.35])
        with left:
            st.plotly_chart(
                coverage_chart(frontier),
                use_container_width=True,
                key="coverage_frontier",
            )
        with right:
            st.plotly_chart(
                priority_map(scenario_scores, candidates, budget),
                use_container_width=True,
                key="plan_priority_map",
            )
        plan_table = selected[
            [
                "candidate_rank",
                "neighborhood",
                "district",
                "nearest_bike_parking_m",
                "marginal_newly_served_grid_points",
                "marginal_weighted_gap_reduction_m",
                "cumulative_weighted_gap_reduction_share",
            ]
        ].copy()
        plan_table = plan_table.rename(
            columns={
                "candidate_rank": "Orden",
                "neighborhood": "Barrio",
                "district": "Distrito",
                "nearest_bike_parking_m": "Distancia actual (m)",
                "marginal_newly_served_grid_points": "Puntos marginales bajo umbral",
                "marginal_weighted_gap_reduction_m": "Ganancia marginal ponderada (m)",
                "cumulative_weighted_gap_reduction_share": "Ganancia acumulada",
            }
        )
        st.dataframe(
            plan_table,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Distancia actual (m)": st.column_config.NumberColumn(format="%.0f"),
                "Ganancia marginal ponderada (m)": st.column_config.NumberColumn(format="%.0f"),
                "Ganancia acumulada": st.column_config.ProgressColumn(
                    format="%.0f%%",
                    min_value=0,
                    max_value=1,
                ),
            },
        )

    with tabs[3]:
        metrics = st.columns(3)
        metrics[0].metric("Moran global I", f"{diagnostics['morans_i']:.3f}")
        metrics[1].metric("p por permutación", f"{diagnostics['permutation_p_value_two_sided']:.3f}")
        metrics[2].metric("Vecinos k-NN", int(diagnostics["knn_neighbors"]))
        left, right = st.columns([1.25, 0.75])
        with left:
            st.plotly_chart(
                spatial_chart(scenario_scores),
                use_container_width=True,
                key="spatial_quadrant_scatter",
            )
        with right:
            quadrants = (
                scenario_scores["spatial_quadrant"]
                .value_counts()
                .rename_axis("Cuadrante")
                .reset_index(name="Barrios")
            )
            st.plotly_chart(
                px.bar(
                    quadrants,
                    x="Cuadrante",
                    y="Barrios",
                    color="Cuadrante",
                    color_discrete_sequence=[COLORS["coral"], COLORS["gold"], COLORS["blue"], "#94A3B8"],
                ).update_layout(**base_layout()),
                use_container_width=True,
                key="spatial_quadrant_counts",
            )
        st.caption(
            "Los cuadrantes describen la posición respecto a la media global y al lag espacial; no son "
            "pruebas locales de significación."
        )

    with tabs[4]:
        st.dataframe(scenario_scores, use_container_width=True, hide_index=True)
        st.download_button(
            "Descargar ranking del escenario actual (CSV)",
            scenario_scores.to_csv(index=False).encode("utf-8"),
            file_name="valencia_bike_equity_scenario.csv",
            mime="text/csv",
        )


if __name__ == "__main__":
    main()
