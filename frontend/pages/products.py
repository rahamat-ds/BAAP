"""Product Analytics — ABC classification and per-product performance."""
import streamlit as st

from analytics.products import abc_classification, category_performance, product_performance
from frontend.common import bootstrap, mapping_hint, require_dataset
from visualization import charts

bootstrap("Product Analytics", "ABC inventory classification and product performance ranking.")

name, df, mapping = require_dataset()

if not (mapping.get("product") and mapping.get("revenue")):
    mapping_hint(["product", "revenue"])
    st.stop()

abc = abc_classification(df, mapping)
perf = product_performance(df, mapping)

c1, c2, c3 = st.columns(3)
c1.metric("Class A products", int((abc["class"] == "A").sum()), help="Top ~80% of revenue")
c2.metric("Class B products", int((abc["class"] == "B").sum()), help="Next ~15% of revenue")
c3.metric("Class C products", int((abc["class"] == "C").sum()), help="Remaining ~5% of revenue")

st.divider()
tab_abc, tab_perf, tab_cat = st.tabs(["ABC Classification", "Product Performance", "Category Breakdown"])

with tab_abc:
    st.plotly_chart(
        charts.scatter(abc, "cum_pct", "revenue", color="class", title="Revenue Concentration (Pareto)"),
        use_container_width=True,
    )
    st.dataframe(abc, use_container_width=True, hide_index=True)

with tab_perf:
    sort_col = "revenue" if "revenue" in perf.columns else perf.columns[-1]
    top = perf.head(15)
    st.plotly_chart(charts.bar(top, perf.columns[0], sort_col, title="Top 15 Products"), use_container_width=True)
    st.dataframe(perf, use_container_width=True, hide_index=True)

with tab_cat:
    cat_perf = category_performance(df, mapping)
    if cat_perf.empty:
        mapping_hint(["category"])
    else:
        st.plotly_chart(charts.treemap(cat_perf, [mapping["category"]], "revenue", title="Revenue by Category"),
                         use_container_width=True)
        st.dataframe(cat_perf, use_container_width=True, hide_index=True)
