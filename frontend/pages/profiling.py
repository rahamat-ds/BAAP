"""Data Profiling — structural overview, column stats, correlations, quality score."""
import streamlit as st

from frontend.common import bootstrap, require_dataset
from pipelines import profiling
from visualization import charts

bootstrap("Data Profiling", "Understand your dataset's shape, types, missingness and quality.")

name, df, mapping = require_dataset()

ov = profiling.overview(df)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Rows", f"{ov.rows:,}")
c2.metric("Columns", ov.columns)
c3.metric("Duplicate Rows", f"{ov.duplicate_rows:,}")
c4.metric("Missing Cells", f"{ov.missing_cells:,}", f"{ov.missing_pct:.1f}%")
c5.metric("Quality Score", f"{ov.quality_score}/100")

st.progress(ov.quality_score / 100)
st.caption(f"Memory usage: {ov.memory_mb:.2f} MB \u00b7 {ov.numeric_cols} numeric columns \u00b7 {ov.text_cols} text columns")

st.divider()
tab_cols, tab_stats, tab_missing, tab_corr = st.tabs(["Column Profile", "Numeric Statistics", "Missing Values", "Correlations"])

with tab_cols:
    st.dataframe(profiling.column_profile(df), use_container_width=True, hide_index=True)

with tab_stats:
    stats = profiling.numeric_stats(df)
    if stats.empty:
        st.caption("No numeric columns detected.")
    else:
        st.dataframe(stats, use_container_width=True)

with tab_missing:
    missing = profiling.missing_summary(df)
    if missing.empty:
        st.success("No missing values \u2014 nice and clean!")
    else:
        st.plotly_chart(charts.bar(missing, "Column", "Missing", title="Missing Values by Column"),
                         use_container_width=True)
        st.dataframe(missing, use_container_width=True, hide_index=True)

with tab_corr:
    corr, strong = profiling.correlations(df)
    if corr.empty:
        st.caption("Need at least 2 numeric columns to compute correlations.")
    else:
        st.plotly_chart(charts.correlation_matrix(corr), use_container_width=True)
        if not strong.empty:
            st.markdown("**Strongly correlated pairs (|r| \u2265 0.5)**")
            st.dataframe(strong, use_container_width=True, hide_index=True)
