"""Data Cleaning — one-click and manual cleaning operations with undo history."""
import streamlit as st

from core.utils import numeric_columns, text_columns
from frontend.common import bootstrap, require_dataset
from pipelines import cleaning
from services import session_service

bootstrap("Data Cleaning", "Fix duplicates, missing values, outliers and formatting issues.")

name, df, mapping = require_dataset()


def _apply(new_df, message):
    session_service.apply_transform(name, new_df, message)
    st.success(message)
    st.rerun()


top1, top2, top3 = st.columns([2, 1, 1])
with top1:
    st.caption(f"Active dataset: **{name}** \u2014 {len(df):,} rows \u00d7 {df.shape[1]} cols")
with top2:
    if st.button("\u2728 Auto-clean", use_container_width=True, help="Dedupe, trim text, and impute missing values in one click"):
        cleaned, report = cleaning.auto_clean(df)
        session_service.apply_transform(
            name, cleaned,
            f"Auto-clean: removed {report['duplicates_removed']} duplicates, filled {report['missing_values_filled']} missing values.",
        )
        st.rerun()
with top3:
    if st.button("\u21a9\ufe0f Undo last step", use_container_width=True, disabled=not session_service.can_undo(name)):
        session_service.undo(name)
        st.rerun()

st.divider()

tab_dup, tab_missing, tab_text, tab_outliers, tab_types, tab_cols = st.tabs(
    ["Duplicates", "Missing Values", "Text & Dates", "Outliers", "Type Conversion", "Columns"]
)

with tab_dup:
    dupes = int(df.duplicated().sum())
    st.metric("Duplicate Rows", f"{dupes:,}")
    subset = st.multiselect("Consider only these columns (optional)", df.columns.tolist(), key="dup_subset")
    if st.button("Remove duplicates", disabled=dupes == 0):
        new_df, msg = cleaning.remove_duplicates(df, subset=subset or None)
        _apply(new_df, msg)

with tab_missing:
    missing_cols = [c for c in df.columns if df[c].isna().any()]
    if not missing_cols:
        st.success("No missing values.")
    else:
        cols = st.multiselect("Columns to fix", missing_cols, default=missing_cols)
        strategy = st.selectbox(
            "Strategy",
            ["drop_rows", "mean", "median", "mode", "zero", "ffill", "bfill", "constant", "drop_columns"],
            format_func=lambda s: {
                "drop_rows": "Drop rows with nulls", "mean": "Fill with mean (numeric)",
                "median": "Fill with median (numeric)", "mode": "Fill with most frequent value",
                "zero": "Fill with 0 (numeric)", "ffill": "Forward fill", "bfill": "Backward fill",
                "constant": "Fill with a constant value", "drop_columns": "Drop the columns entirely",
            }[s],
        )
        fill_value = st.text_input("Constant value", "") if strategy == "constant" else None
        if st.button("Apply", disabled=not cols, key="apply_missing"):
            new_df, msg = cleaning.handle_missing(df, strategy=strategy, columns=cols, fill_value=fill_value)
            _apply(new_df, msg)

with tab_text:
    tcols = text_columns(df)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Fix text case**")
        sel = st.multiselect("Columns", tcols, key="case_cols")
        mode = st.selectbox("Case", ["title", "lower", "upper", "capitalize"])
        if st.button("Apply case fix", disabled=not sel):
            new_df, msg = cleaning.fix_text_case(df, sel, mode)
            _apply(new_df, msg)
        st.markdown("**Trim whitespace**")
        if st.button("Trim all text columns"):
            new_df, msg = cleaning.trim_whitespace(df)
            _apply(new_df, msg)
    with c2:
        st.markdown("**Standardize dates**")
        date_candidates = [c for c in df.columns if "date" in str(c).lower()]
        dsel = st.multiselect("Date columns", date_candidates or df.columns.tolist(), key="date_cols")
        if st.button("Standardize", disabled=not dsel):
            new_df, msg = cleaning.standardize_dates(df, dsel)
            _apply(new_df, msg)

with tab_outliers:
    ncols = numeric_columns(df)
    if not ncols:
        st.caption("No numeric columns detected.")
    else:
        sel = st.multiselect("Numeric columns", ncols, key="outlier_cols")
        method = st.radio("Method", ["iqr", "zscore"], horizontal=True)
        factor = st.slider("Sensitivity factor", 1.0, 4.0, 1.5, 0.1)
        action = st.radio("Action", ["remove", "clip"], horizontal=True, format_func=lambda a: "Remove rows" if a == "remove" else "Clip to bounds")
        if st.button("Apply", disabled=not sel, key="apply_outliers"):
            new_df, msg = cleaning.remove_outliers(df, sel, method=method, factor=factor, action=action)
            _apply(new_df, msg)

with tab_types:
    col = st.selectbox("Column", df.columns.tolist())
    st.caption(f"Current type: `{df[col].dtype}`")
    target = st.selectbox("Convert to", ["numeric", "integer", "datetime", "string", "category", "boolean"])
    if st.button("Convert"):
        new_df, msg = cleaning.convert_types(df, col, target)
        _apply(new_df, msg)

with tab_cols:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Drop columns**")
        drop_sel = st.multiselect("Columns to drop", df.columns.tolist())
        if st.button("Drop", disabled=not drop_sel):
            new_df, msg = cleaning.drop_columns(df, drop_sel)
            _apply(new_df, msg)
    with c2:
        st.markdown("**Normalize all column names**")
        st.caption("Converts headers to consistent snake_case.")
        if st.button("Normalize column names"):
            new_df, msg = cleaning.clean_column_names(df)
            _apply(new_df, msg)

st.divider()
st.markdown("#### Cleaning log")
log = session_service.cleaning_log(name)
if not log:
    st.caption("No cleaning steps applied yet.")
else:
    for i, entry in enumerate(reversed(log), 1):
        st.caption(f"{len(log) - i + 1}. {entry}")
