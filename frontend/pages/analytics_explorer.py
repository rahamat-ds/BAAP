"""Analytics — sales, product and customer deep-dive built from the column mapping."""
import streamlit as st

from analytics.insights import rule_based_insights
from analytics.kpis import compute_core_kpis, top_n
from analytics.products import category_performance
from frontend.common import bootstrap, mapping_hint, require_dataset
from visualization import charts
from visualization.theme import render_kpi_row

bootstrap("Analytics", "A guided deep-dive across sales, products and customers.")

name, df, mapping = require_dataset()
revenue_c, profit_c = mapping.get("revenue"), mapping.get("profit")
category_c, region_c, product_c, customer_c = (
    mapping.get("category"), mapping.get("region"), mapping.get("product"), mapping.get("customer_id"),
)

tab_intel, tab_sales, tab_products, tab_customers = st.tabs(
    ["\U0001f9e0 Intelligence", "\U0001f4ca Sales", "\U0001f4e6 Products", "\U0001f465 Customers"]
)

with tab_intel:
    st.markdown("#### Automated Insights")
    for insight in rule_based_insights(df, mapping):
        st.markdown(f"- {insight}")
    st.divider()
    st.markdown("#### KPI Summary")
    render_kpi_row(compute_core_kpis(df, mapping), currency_fields={"Total Revenue", "Total Profit", "Avg Order Value"})

with tab_sales:
    if not (revenue_c and category_c):
        mapping_hint(["revenue", "category"])
    else:
        left, right = st.columns(2)
        with left:
            cat_perf = category_performance(df, mapping)
            st.plotly_chart(charts.pie(cat_perf, category_c, "revenue", title="Revenue Share by Category"),
                             use_container_width=True)
        with right:
            if profit_c:
                prof = df.groupby(category_c, dropna=False)[profit_c].sum().reset_index()
                st.plotly_chart(charts.pie(prof, category_c, profit_c, title="Profit Share by Category"),
                                 use_container_width=True)
            else:
                st.caption("Map a **profit** column to see profit contribution.")

        if region_c:
            st.divider()
            st.markdown("#### Regional Performance")
            region_perf = top_n(df, region_c, revenue_c, n=20)
            st.dataframe(region_perf, use_container_width=True, hide_index=True)
            st.plotly_chart(charts.bar(region_perf, region_c, revenue_c, title=f"Revenue by {region_c}"),
                             use_container_width=True)

with tab_products:
    if not (product_c and revenue_c):
        mapping_hint(["product", "revenue"])
    else:
        top = top_n(df, product_c, revenue_c, n=10)
        bottom = (
            df.assign(__v=df[revenue_c])
            .groupby(product_c, dropna=False)["__v"].sum()
            .sort_values(ascending=True).head(10).reset_index().rename(columns={"__v": revenue_c})
        )
        left, right = st.columns(2)
        with left:
            st.markdown("**Top 10 Products**")
            st.plotly_chart(charts.bar(top, product_c, revenue_c, title="Top Products"), use_container_width=True)
        with right:
            st.markdown("**Bottom 10 Products**")
            st.plotly_chart(charts.bar(bottom, product_c, revenue_c, title="Underperforming Products"),
                             use_container_width=True)
        st.caption("For full ABC classification and per-product profit/units, see **Product Analytics**.")

with tab_customers:
    if not (customer_c and revenue_c):
        mapping_hint(["customer_id", "revenue"])
    else:
        top_cust = top_n(df, customer_c, revenue_c, n=15)
        st.markdown("**Top 15 Customers by Revenue**")
        st.dataframe(top_cust, use_container_width=True, hide_index=True)
        st.plotly_chart(charts.bar(top_cust, customer_c, revenue_c, title="Top Customers"), use_container_width=True)
        st.caption("For RFM segmentation and lifetime value, see **Customer Analytics**.")
