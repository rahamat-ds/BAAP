"""Dashboard — headline KPIs, trend, and top breakdowns for the active dataset."""
import streamlit as st

from analytics.kpis import compute_core_kpis, revenue_by_period, top_n
from frontend.common import bootstrap, require_dataset
from pipelines.profiling import quality_score
from visualization import charts
from visualization.theme import render_kpi_row

bootstrap("Dashboard", "A live overview of your active dataset.")

name, df, mapping = require_dataset()

kpis = compute_core_kpis(df, mapping)
render_kpi_row(kpis, currency_fields={"Total Revenue", "Total Profit", "Total Profit (est.)", "Avg Order Value", "Revenue / Customer"})

st.divider()

date_c, revenue_c = mapping.get("date"), mapping.get("revenue")
if date_c and revenue_c:
    freq = st.radio("Trend granularity", ["D", "W", "M"], index=2, horizontal=True,
                     format_func=lambda f: {"D": "Daily", "W": "Weekly", "M": "Monthly"}[f])
    trend = revenue_by_period(df, mapping, freq=freq)
    if not trend.empty:
        st.plotly_chart(charts.area(trend, "period", "value", title=f"{revenue_c} Trend"), use_container_width=True)
else:
    st.caption("Map a **date** and **revenue** column in Upload Center to see the trend chart.")

col1, col2 = st.columns(2)
with col1:
    cat_c = mapping.get("category") or mapping.get("product")
    if cat_c and revenue_c:
        top = top_n(df, cat_c, revenue_c, n=8)
        if not top.empty:
            st.plotly_chart(charts.bar(top, cat_c, revenue_c, title=f"Top {cat_c} by {revenue_c}"),
                             use_container_width=True)
with col2:
    region_c = mapping.get("region")
    if region_c and revenue_c:
        top = top_n(df, region_c, revenue_c, n=8)
        if not top.empty:
            st.plotly_chart(charts.donut(top, region_c, revenue_c, title=f"Revenue by {region_c}"),
                             use_container_width=True)

st.divider()
score = quality_score(df)
c1, c2, c3 = st.columns(3)
c1.metric("Data Quality Score", f"{score}/100")
c2.metric("Duplicate Rows", f"{int(df.duplicated().sum()):,}")
c3.metric("Missing Cells", f"{int(df.isna().sum().sum()):,}")

with st.expander("Preview data"):
    st.dataframe(df.head(50), use_container_width=True)
