"""Customer Analytics — RFM segmentation, lifetime value, churn risk."""
import streamlit as st

from analytics.customers import churn_risk, customer_lifetime_value, rfm_analysis, segment_summary
from frontend.common import bootstrap, mapping_hint, require_dataset
from visualization import charts

bootstrap("Customer Analytics", "RFM segmentation, lifetime value estimation, and churn risk.")

name, df, mapping = require_dataset()

if not (mapping.get("customer_id") and mapping.get("date") and mapping.get("revenue")):
    mapping_hint(["customer_id", "date", "revenue"])
    st.stop()

rfm = rfm_analysis(df, mapping)
if rfm.empty:
    st.warning("Not enough data to compute RFM segments (need multiple customers with dated transactions).")
    st.stop()

rfm = customer_lifetime_value(rfm)
threshold = st.slider("Churn-risk threshold (days since last purchase)", 30, 365, 90, 15)
rfm = churn_risk(rfm, recency_threshold_days=threshold)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Customers", f"{len(rfm):,}")
c2.metric("Champions", int((rfm["segment"] == "Champions").sum()))
c3.metric("At Risk", int((rfm["segment"] == "At Risk").sum()))
c4.metric("Churn Risk (>{}d)".format(threshold), int(rfm["churn_risk"].sum()))

st.divider()
tab_segments, tab_clv, tab_table = st.tabs(["Segments", "Lifetime Value", "Full Table"])

with tab_segments:
    summary = segment_summary(rfm)
    left, right = st.columns(2)
    with left:
        st.plotly_chart(charts.donut(summary, "segment", "customers", title="Customers by Segment"), use_container_width=True)
    with right:
        st.plotly_chart(charts.bar(summary, "segment", "total_value", title="Value by Segment"), use_container_width=True)
    st.dataframe(summary, use_container_width=True, hide_index=True)

with tab_clv:
    top_clv = rfm.sort_values("estimated_clv", ascending=False).head(20)
    st.plotly_chart(charts.bar(top_clv, "customer", "estimated_clv", title="Top 20 Customers by Estimated CLV"),
                     use_container_width=True)
    st.caption("CLV = average order value \u00d7 purchase frequency \u00d7 assumed 2-year customer lifespan.")

with tab_table:
    st.dataframe(rfm, use_container_width=True, hide_index=True)
