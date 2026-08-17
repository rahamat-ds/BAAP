"""Anomaly Detection — z-score, IQR, Isolation Forest, and time-series anomalies."""
import streamlit as st

from core.utils import numeric_columns
from forecasting import anomalies
from frontend.common import bootstrap, require_dataset
from visualization import charts

bootstrap("Anomaly Detection", "Find unusual rows and unusual days in your data.")

name, df, mapping = require_dataset()
ncols = numeric_columns(df)

tab_column, tab_multivariate, tab_timeseries = st.tabs(
    ["\U0001f4cf Single Column", "\U0001f9e9 Multivariate (Isolation Forest)", "\U0001f4c6 Time Series"]
)

with tab_column:
    if not ncols:
        st.caption("No numeric columns detected.")
    else:
        col = st.selectbox("Column", ncols)
        method = st.radio("Method", ["zscore", "iqr"], horizontal=True,
                           format_func=lambda m: "Z-Score" if m == "zscore" else "IQR")
        threshold = st.slider("Sensitivity", 1.5, 5.0, 3.0, 0.1) if method == "zscore" else st.slider("IQR factor", 1.0, 4.0, 1.5, 0.1)
        result = anomalies.detect_zscore(df, col, threshold) if method == "zscore" else anomalies.detect_iqr(df, col, threshold)
        st.metric("Anomalies found", f"{len(result):,}", f"{len(result) / max(len(df), 1) * 100:.2f}% of rows")
        if not result.empty:
            st.plotly_chart(charts.box(df, col, title=f"Distribution of {col} (outliers highlighted separately below)"),
                             use_container_width=True)
            st.dataframe(result, use_container_width=True)

with tab_multivariate:
    if len(ncols) < 2:
        st.caption("Need at least 2 numeric columns for multivariate anomaly detection.")
    else:
        cols = st.multiselect("Columns to consider", ncols, default=ncols[: min(4, len(ncols))])
        contamination = st.slider("Expected anomaly rate", 0.01, 0.20, 0.03, 0.01)
        if cols and st.button("Run Isolation Forest"):
            result = anomalies.detect_isolation_forest(df, cols, contamination=contamination)
            st.metric("Anomalies found", f"{len(result):,}")
            st.dataframe(result, use_container_width=True)
            if len(cols) >= 2:
                st.plotly_chart(
                    charts.scatter(df.assign(_flag=df.index.isin(result.index)), cols[0], cols[1], color="_flag",
                                    title=f"{cols[1]} vs {cols[0]} (anomalies flagged)"),
                    use_container_width=True,
                )

with tab_timeseries:
    if not (mapping.get("date") and mapping.get("revenue")):
        st.caption("Map a **date** and **revenue** column in Upload Center to detect time-series anomalies.")
    else:
        threshold = st.slider("Sensitivity (z-score)", 1.5, 5.0, 3.0, 0.1, key="ts_thresh")
        result = anomalies.detect_time_series_anomalies(df, mapping, threshold=threshold)
        if result.empty:
            st.info("No anomalous days detected at this sensitivity.")
        else:
            st.metric("Anomalous days", len(result))
            st.plotly_chart(charts.scatter(result, "date", "value", color="z_score", title="Anomalous Days"),
                             use_container_width=True)
            st.dataframe(result, use_container_width=True)
