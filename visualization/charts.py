"""Plotly chart factory: one function per chart type, all pre-themed."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from visualization.theme import PLOTLY_TEMPLATE


def _themed(fig: go.Figure, title: str = "") -> go.Figure:
    fig.update_layout(PLOTLY_TEMPLATE["layout"])
    if title:
        fig.update_layout(title=title)
    return fig


def bar(df: pd.DataFrame, x: str, y: str, color: str | None = None, title: str = "", orientation: str = "v") -> go.Figure:
    fig = px.bar(df, x=x if orientation == "v" else y, y=y if orientation == "v" else x,
                 color=color, orientation=orientation)
    return _themed(fig, title)


def line(df: pd.DataFrame, x: str, y: str, color: str | None = None, title: str = "") -> go.Figure:
    fig = px.line(df, x=x, y=y, color=color, markers=True)
    return _themed(fig, title)


def area(df: pd.DataFrame, x: str, y: str, color: str | None = None, title: str = "") -> go.Figure:
    fig = px.area(df, x=x, y=y, color=color)
    return _themed(fig, title)


def pie(df: pd.DataFrame, names: str, values: str, title: str = "", hole: float = 0.0) -> go.Figure:
    fig = px.pie(df, names=names, values=values, hole=hole)
    return _themed(fig, title)


def donut(df: pd.DataFrame, names: str, values: str, title: str = "") -> go.Figure:
    return pie(df, names, values, title, hole=0.55)


def scatter(df: pd.DataFrame, x: str, y: str, color: str | None = None, size: str | None = None, title: str = "") -> go.Figure:
    fig = px.scatter(df, x=x, y=y, color=color, size=size)
    return _themed(fig, title)


def bubble(df: pd.DataFrame, x: str, y: str, size: str, color: str | None = None, title: str = "") -> go.Figure:
    fig = px.scatter(df, x=x, y=y, size=size, color=color, size_max=45)
    return _themed(fig, title)


def histogram(df: pd.DataFrame, x: str, nbins: int = 30, title: str = "") -> go.Figure:
    fig = px.histogram(df, x=x, nbins=nbins)
    return _themed(fig, title)


def box(df: pd.DataFrame, y: str, x: str | None = None, title: str = "") -> go.Figure:
    fig = px.box(df, x=x, y=y, points="outliers")
    return _themed(fig, title)


def heatmap(matrix: pd.DataFrame, title: str = "") -> go.Figure:
    fig = go.Figure(data=go.Heatmap(
        z=matrix.values, x=matrix.columns.astype(str), y=matrix.index.astype(str),
        colorscale="RdBu", zmid=0, text=matrix.round(2).values, texttemplate="%{text}",
    ))
    return _themed(fig, title)


def treemap(df: pd.DataFrame, path: list[str], values: str, title: str = "") -> go.Figure:
    fig = px.treemap(df, path=path, values=values)
    return _themed(fig, title)


def sunburst(df: pd.DataFrame, path: list[str], values: str, title: str = "") -> go.Figure:
    fig = px.sunburst(df, path=path, values=values)
    return _themed(fig, title)


def waterfall(categories: list[str], values: list[float], title: str = "") -> go.Figure:
    fig = go.Figure(go.Waterfall(
        x=categories, y=values,
        measure=["relative"] * (len(values) - 1) + ["total"],
        connector={"line": {"color": "#2A2E3D"}},
    ))
    return _themed(fig, title)


def correlation_matrix(corr: pd.DataFrame, title: str = "Correlation Matrix") -> go.Figure:
    return heatmap(corr, title)


def forecast_chart(forecast_df: pd.DataFrame, title: str = "Forecast") -> go.Figure:
    """Actual vs forecast line chart with a shaded confidence band."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=forecast_df["date"], y=forecast_df["actual"], name="Actual",
                              mode="lines", line={"color": "#6C5CE7", "width": 2}))
    fig.add_trace(go.Scatter(x=forecast_df["date"], y=forecast_df["forecast"], name="Forecast",
                              mode="lines", line={"color": "#00B8A9", "width": 2, "dash": "dash"}))
    fig.add_trace(go.Scatter(
        x=pd.concat([forecast_df["date"], forecast_df["date"][::-1]]),
        y=pd.concat([forecast_df["upper"], forecast_df["lower"][::-1]]),
        fill="toself", fillcolor="rgba(0,184,169,0.15)", line={"color": "rgba(0,0,0,0)"},
        name="Confidence Band", showlegend=True,
    ))
    return _themed(fig, title)


CHART_FUNCS = {
    "Bar": bar, "Line": line, "Area": area, "Pie": pie, "Donut": donut,
    "Scatter": scatter, "Bubble": bubble, "Histogram": histogram, "Box Plot": box,
    "Heatmap": heatmap, "Treemap": treemap, "Sunburst": sunburst,
    "Waterfall": waterfall, "Correlation Matrix": correlation_matrix,
}
