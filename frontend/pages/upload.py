"""Upload Center — load data, manage multiple datasets, and edit column mapping."""
import pandas as pd
import streamlit as st

from config import ROLE_LABELS, ROLES
from frontend.common import bootstrap
from pipelines import ingestion
from services import dataset_service, session_service

bootstrap("Upload Center", "Load one or more datasets, then map their columns to InsightFlow's analysis roles.")

tab_upload, tab_sample, tab_sql, tab_manage, tab_mapping = st.tabs(
    ["\U0001f4c1 Upload File", "\u26a1 Sample Data", "\U0001f5c4\ufe0f Connect Database", "\U0001f4da Manage Datasets", "\U0001f9ed Column Mapping"]
)

# --------------------------------------------------------------------------
with tab_upload:
    st.markdown("Supports **CSV, Excel (multi-sheet), JSON, ZIP archives, and SQLite files**.")
    uploaded = st.file_uploader(
        "Drop a file here", type=["csv", "txt", "xlsx", "xls", "xlsm", "json", "zip", "db", "sqlite", "sqlite3"],
    )
    if uploaded is not None:
        raw = uploaded.getvalue()
        size_mb = len(raw) / 1024**2
        st.caption(f"{uploaded.name} \u2014 {size_mb:.2f} MB")
        try:
            frames = dataset_service.load_uploaded_file(uploaded.name, raw)
        except Exception as exc:  # noqa: BLE001
            st.error(f"Couldn't parse this file: {exc}")
            frames = []

        for suggested_name, df, meta in frames:
            with st.expander(f"\U0001f4c4 {suggested_name}  ({len(df):,} rows \u00d7 {df.shape[1]} cols)", expanded=len(frames) == 1):
                for level, message in ingestion.validate_upload(df):
                    (st.success if level == "ok" else st.warning if level == "warn" else st.error)(message)
                st.dataframe(df.head(10), use_container_width=True)
                if st.button("Add to workspace", key=f"add_{suggested_name}"):
                    registered = dataset_service.register_and_log(suggested_name, df, source="upload")
                    st.success(f"Loaded as '{registered}'.")
                    st.rerun()

# --------------------------------------------------------------------------
with tab_sample:
    st.markdown(
        "Generate a realistic **Indian e-commerce retail orders** dataset — customers, products, "
        "logistics, RTO/returns, revenue and profit — with a small amount of intentional data-quality "
        "issues so you can try the cleaning and validation tools."
    )
    n_orders = st.slider("Number of orders", 500, 50_000, 6000, step=500)
    seed = st.number_input("Random seed (for reproducibility)", value=42, step=1)
    if st.button("\u26a1 Generate sample dataset", type="primary"):
        with st.spinner(f"Generating {n_orders:,} synthetic orders..."):
            from services.sample_data_service import generate_dataset

            df = generate_dataset(n_orders=int(n_orders), seed=int(seed))
            registered = dataset_service.register_and_log("Indian_Retail_Orders", df, source="sample")
        st.success(f"Generated and loaded as '{registered}'.")
        st.rerun()

# --------------------------------------------------------------------------
with tab_sql:
    st.markdown("Connect to any **SQLAlchemy-compatible** database URI (e.g. `sqlite:///path.db`, `postgresql://...`).")
    uri = st.text_input("Database URI", placeholder="sqlite:///data/mydata.db")
    if uri and st.button("Load tables"):
        try:
            frames = ingestion.sql_tables(uri, limit=200_000)
        except Exception as exc:  # noqa: BLE001
            st.error(f"Connection failed: {exc}")
            frames = {}
        for table_name, df in frames.items():
            registered = dataset_service.register_and_log(table_name, df, source="sql")
            st.success(f"Loaded table '{table_name}' as '{registered}' ({len(df):,} rows).")
        if frames:
            st.rerun()

# --------------------------------------------------------------------------
with tab_manage:
    names = session_service.dataset_names()
    if not names:
        st.info("No datasets loaded yet.")
    for n in names:
        df = session_service.get_df(n)
        c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
        c1.markdown(f"**{n}**")
        c2.caption(f"{len(df):,} rows \u00d7 {df.shape[1]} cols")
        if c3.button("Activate", key=f"act_{n}", disabled=(n == session_service.active_name())):
            session_service.set_active(n)
            st.rerun()
        if c4.button("\U0001f5d1\ufe0f", key=f"del_{n}", help="Remove dataset"):
            session_service.remove_dataset(n)
            st.rerun()

# --------------------------------------------------------------------------
with tab_mapping:
    names = session_service.dataset_names()
    if not names:
        st.info("Load a dataset first.")
    else:
        target = st.selectbox("Dataset to map", names, index=names.index(session_service.active_name()))
        df = session_service.get_df(target)
        mapping = session_service.get_mapping(target)
        st.caption("InsightFlow auto-detects these roles from your column names and types. Override any of them below.")

        cols = st.columns(2)
        new_mapping = {}
        options = ["(none)"] + list(df.columns)
        for i, role in enumerate(ROLES):
            with cols[i % 2]:
                current = mapping.get(role)
                index = options.index(current) if current in options else 0
                choice = st.selectbox(ROLE_LABELS[role], options, index=index, key=f"map_{target}_{role}")
                new_mapping[role] = None if choice == "(none)" else choice

        if st.button("Save mapping", type="primary"):
            session_service.set_mapping(target, new_mapping)
            st.success("Mapping saved.")
            st.rerun()

        filled = sum(1 for v in new_mapping.values() if v)
        st.progress(filled / len(ROLES), text=f"{filled}/{len(ROLES)} roles mapped")
