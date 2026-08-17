"""Retail Operations — courier performance, RTO/returns, shipping analysis.

InsightFlow's original logistics-analytics differentiator. Fully optional:
it auto-detects its own extended roles and shows a friendly explanation
when a dataset doesn't carry retail-operations columns (e.g. generic
non-retail datasets), rather than an empty or broken page.
"""
import streamlit as st

from analytics import retail
from frontend.common import bootstrap, require_dataset
from visualization import charts

bootstrap("Retail Operations",
          "Courier performance, RTO/returns, and shipping analysis for order/logistics data.")

name, df, mapping = require_dataset()
retail_mapping = retail.detect(df, mapping)

if not retail.is_applicable(retail_mapping):
    st.info(
        "This module activates automatically for order datasets with courier, shipping-mode, "
        "delivery-time or RTO/return columns \u2014 like the bundled **Indian Retail Orders** sample. "
        "Your active dataset doesn't appear to have these, so there's nothing to show here yet."
    )
    st.caption("Try loading the sample dataset from Upload Center to see this module in action.")
    st.stop()

detected = ", ".join(f"{k} \u2192 {v}" for k, v in retail_mapping.items() if v)
st.caption(f"Detected retail-operations columns: {detected}")

tab_courier, tab_rto, tab_shipping = st.tabs(["\U0001f69a Courier Performance", "\u21a9\ufe0f RTO / Returns", "\U0001f4e6 Shipping"])

with tab_courier:
    perf = retail.courier_performance(df, mapping, retail_mapping)
    if perf.empty:
        st.caption("No courier column detected.")
    else:
        courier_c = retail_mapping["courier"]
        st.dataframe(perf, use_container_width=True, hide_index=True)
        left, right = st.columns(2)
        with left:
            st.plotly_chart(charts.bar(perf, courier_c, "orders", title="Orders by Courier"), use_container_width=True)
        with right:
            if "rto_rate_pct" in perf.columns:
                st.plotly_chart(charts.bar(perf, courier_c, "rto_rate_pct", title="RTO Rate % by Courier"),
                                 use_container_width=True)

with tab_rto:
    summary = retail.rto_analysis(df, retail_mapping)
    if summary.empty:
        st.caption("No RTO/return column detected.")
    else:
        row = summary.iloc[0]
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Orders", f"{int(row['total_orders']):,}")
        c2.metric("RTO Orders", f"{int(row['rto_orders']):,}")
        c3.metric("RTO Rate", f"{row['rto_rate_pct']:.2f}%")

with tab_shipping:
    breakdown = retail.shipping_mode_breakdown(df, retail_mapping)
    if breakdown.empty:
        st.caption("No shipping-mode column detected.")
    else:
        mode_c = retail_mapping["shipping_mode"]
        st.dataframe(breakdown, use_container_width=True, hide_index=True)
        st.plotly_chart(charts.pie(breakdown, mode_c, "orders", title="Orders by Shipping Mode"),
                         use_container_width=True)

    dist = retail.delivery_time_distribution(df, retail_mapping)
    if not dist.empty:
        st.plotly_chart(charts.histogram(dist, "delivery_days", title="Delivery Time Distribution (days)"),
                         use_container_width=True)
