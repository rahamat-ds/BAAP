"""Visualizations — build any of 14 chart types over the active dataset."""
import streamlit as st

from config import AGGREGATIONS, CHART_TYPES
from core.utils import numeric_columns, text_columns
from frontend.common import bootstrap, require_dataset
from pipelines.profiling import correlations
from visualization import charts

bootstrap("Visualizations", "Build beautiful, interactive charts from any columns.")

name, df, mapping = require_dataset()
ncols, tcols, allcols = numeric_columns(df), text_columns(df), df.columns.tolist()

chart_type = st.selectbox("Chart type", CHART_TYPES)

fig = None
try:
    if chart_type in ("Bar", "Line", "Area"):
        c1, c2, c3 = st.columns(3)
        x = c1.selectbox("X axis", allcols)
        y = c2.selectbox("Y axis", ncols or allcols)
        color = c3.selectbox("Color (optional)", ["(none)"] + tcols)
        color = None if color == "(none)" else color
        fig = getattr(charts, chart_type.lower())(df, x, y, color=color, title=f"{y} by {x}")

    elif chart_type in ("Pie", "Donut"):
        c1, c2 = st.columns(2)
        names = c1.selectbox("Categories", tcols or allcols)
        values = c2.selectbox("Values", ncols or allcols)
        fn = charts.donut if chart_type == "Donut" else charts.pie
        fig = fn(df, names, values, title=f"{values} by {names}")

    elif chart_type == "Scatter":
        c1, c2, c3 = st.columns(3)
        x = c1.selectbox("X axis", ncols or allcols)
        y = c2.selectbox("Y axis", ncols or allcols, index=min(1, len(ncols or allcols) - 1))
        color = c3.selectbox("Color (optional)", ["(none)"] + tcols)
        fig = charts.scatter(df, x, y, color=None if color == "(none)" else color, title=f"{y} vs {x}")

    elif chart_type == "Bubble":
        c1, c2, c3, c4 = st.columns(4)
        x = c1.selectbox("X axis", ncols)
        y = c2.selectbox("Y axis", ncols, index=min(1, len(ncols) - 1))
        size = c3.selectbox("Size", ncols, index=min(2, len(ncols) - 1))
        color = c4.selectbox("Color (optional)", ["(none)"] + tcols)
        fig = charts.bubble(df, x, y, size, color=None if color == "(none)" else color, title=f"{y} vs {x} (size: {size})")

    elif chart_type == "Histogram":
        x = st.selectbox("Column", ncols or allcols)
        nbins = st.slider("Bins", 5, 100, 30)
        fig = charts.histogram(df, x, nbins=nbins, title=f"Distribution of {x}")

    elif chart_type == "Box Plot":
        c1, c2 = st.columns(2)
        y = c1.selectbox("Value", ncols or allcols)
        x = c2.selectbox("Group by (optional)", ["(none)"] + tcols)
        fig = charts.box(df, y, x=None if x == "(none)" else x, title=f"Distribution of {y}")

    elif chart_type == "Heatmap":
        corr, _ = correlations(df, threshold=0.0)
        if corr.empty:
            st.caption("Need at least 2 numeric columns.")
        else:
            fig = charts.heatmap(corr, title="Numeric Correlation Heatmap")

    elif chart_type in ("Treemap", "Sunburst"):
        path = st.multiselect("Hierarchy (order matters)", tcols, default=tcols[:2] if len(tcols) >= 2 else tcols)
        values = st.selectbox("Values", ncols or allcols)
        if path:
            fn = charts.sunburst if chart_type == "Sunburst" else charts.treemap
            fig = fn(df, path, values, title=f"{values} by {' > '.join(path)}")

    elif chart_type == "Waterfall":
        cat_col = st.selectbox("Category", tcols or allcols)
        val_col = st.selectbox("Value", ncols or allcols)
        agg = df.groupby(cat_col, dropna=False)[val_col].sum().sort_values(ascending=False).head(12)
        fig = charts.waterfall(agg.index.astype(str).tolist(), agg.values.tolist(), title=f"{val_col} Waterfall by {cat_col}")

    elif chart_type == "Correlation Matrix":
        corr, _ = correlations(df, threshold=0.0)
        if corr.empty:
            st.caption("Need at least 2 numeric columns.")
        else:
            fig = charts.correlation_matrix(corr)

except Exception as exc:  # noqa: BLE001
    st.error(f"Couldn't build this chart with the selected columns: {exc}")

if fig is not None:
    st.plotly_chart(fig, use_container_width=True)
