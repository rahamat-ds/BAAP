"""Transformation — group-by, pivot, merge, feature engineering."""
import streamlit as st

from core.utils import numeric_columns
from frontend.common import bootstrap, require_dataset
from pipelines import transform
from services import session_service

bootstrap("Transformation", "Reshape and enrich your data: group-by, pivot, merge, binning and feature engineering.")

name, df, mapping = require_dataset()

tab_group, tab_pivot, tab_merge, tab_feature, tab_calc = st.tabs(
    ["Group & Aggregate", "Pivot Table", "Merge Datasets", "Feature Engineering", "Calculated Column"]
)


def _apply(new_df, message):
    session_service.apply_transform(name, new_df, message)
    st.success(message)
    st.rerun()


with tab_group:
    group_cols = st.multiselect("Group by", df.columns.tolist())
    ncols = numeric_columns(df)
    agg_map = {}
    for c in st.multiselect("Aggregate columns", ncols):
        agg_map[c] = st.selectbox(f"Aggregation for {c}", ["sum", "mean", "count", "min", "max", "median"], key=f"agg_{c}")
    if st.button("Run group-by", disabled=not (group_cols and agg_map)):
        result = transform.group_and_aggregate(df, group_cols, agg_map)
        st.dataframe(result, use_container_width=True)
        if st.button("Replace active dataset with this result"):
            _apply(result, f"Grouped by {', '.join(group_cols)}.")

with tab_pivot:
    c1, c2, c3 = st.columns(3)
    index = c1.selectbox("Rows (index)", df.columns.tolist())
    columns = c2.selectbox("Columns", df.columns.tolist())
    values = c3.selectbox("Values", numeric_columns(df) or df.columns.tolist())
    aggfunc = st.selectbox("Aggregation", ["sum", "mean", "count", "min", "max"])
    if st.button("Build pivot table"):
        try:
            result = transform.pivot(df, index, columns, values, aggfunc)
            st.dataframe(result, use_container_width=True)
        except Exception as exc:  # noqa: BLE001
            st.error(f"Couldn't build pivot: {exc}")

with tab_merge:
    others = [n for n in session_service.dataset_names() if n != name]
    if not others:
        st.info("Load a second dataset in Upload Center to merge it with the active one.")
    else:
        other_name = st.selectbox("Merge with", others)
        other_df = session_service.get_df(other_name)
        common_cols = [c for c in df.columns if c in other_df.columns]
        on = st.multiselect("Join on", common_cols or df.columns.tolist())
        how = st.selectbox("Join type", ["inner", "left", "right", "outer"])
        if st.button("Merge", disabled=not on):
            result = transform.merge_datasets(df, other_df, on=on, how=how)
            st.success(f"Merged into {len(result):,} rows.")
            st.dataframe(result.head(50), use_container_width=True)
            if st.button("Register merged result as a new dataset"):
                from services import dataset_service

                dataset_service.register_and_log(f"{name}_merged_{other_name}", result, source="merge")
                st.rerun()

with tab_feature:
    date_candidates = [c for c in df.columns if "date" in str(c).lower()]
    if date_candidates:
        dc = st.selectbox("Extract date parts from", date_candidates)
        if st.button("Add date part columns"):
            _apply(transform.add_date_parts(df, dc), f"Added date-part columns from '{dc}'.")
    st.divider()
    ncols = numeric_columns(df)
    if ncols:
        bc = st.selectbox("Bin a numeric column", ncols)
        bins = st.slider("Number of bins", 2, 10, 5)
        if st.button("Add binned column"):
            _apply(transform.bin_column(df, bc, bins), f"Binned '{bc}' into {bins} groups.")

with tab_calc:
    st.caption("Write a pandas expression using existing column names, e.g. `revenue - cost`.")
    new_col = st.text_input("New column name", "calculated_value")
    expr = st.text_input("Expression", placeholder="revenue - cost")
    if st.button("Create column", disabled=not expr):
        try:
            _apply(transform.create_calculated_column(df, new_col, expr), f"Added calculated column '{new_col}'.")
        except Exception as exc:  # noqa: BLE001
            st.error(f"Couldn't evaluate expression: {exc}")
