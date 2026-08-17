"""SQL Workspace — query any loaded dataset with real SQL via an in-memory engine."""
import sqlite3

import pandas as pd
import streamlit as st

from database import repository
from frontend.common import bootstrap, require_dataset
from services import session_service

bootstrap("SQL Workspace", "Run real SQL against your loaded datasets via an in-memory SQLite engine.")

name, df, mapping = require_dataset()
sid = session_service.session_id()

names = session_service.dataset_names()
st.caption("Every loaded dataset is available as a table named after it (spaces and symbols become underscores).")


def _table_name(dataset_name: str) -> str:
    import re

    return re.sub(r"\W+", "_", dataset_name).strip("_").lower() or "dataset"


table_map = {n: _table_name(n) for n in names}
with st.expander("Available tables", expanded=True):
    for n, t in table_map.items():
        d = session_service.get_df(n)
        st.code(f"{t}   -- {len(d):,} rows, {d.shape[1]} cols  (from '{n}')", language=None)

default_table = table_map[name]
default_query = st.session_state.pop("_prefill_query", f"SELECT * FROM {default_table} LIMIT 100")
query = st.text_area("SQL query", value=default_query, height=140)

col1, col2 = st.columns([1, 4])
run = col1.button("\u25b6\ufe0f Run query", type="primary")
save_name = col2.text_input("Save as (optional)", label_visibility="collapsed", placeholder="Name to save this query as...")

if run:
    try:
        conn = sqlite3.connect(":memory:")
        for n, t in table_map.items():
            session_service.get_df(n).to_sql(t, conn, index=False, if_exists="replace")
        result = pd.read_sql_query(query, conn)
        conn.close()
        st.session_state["_sql_result"] = result
        repository.log_activity(sid, "sql_query", {"query": query[:200]})
        if save_name:
            repository.save_query(sid, save_name, query)
            st.toast(f"Saved query as '{save_name}'")
    except Exception as exc:  # noqa: BLE001
        st.error(f"Query failed: {exc}")
        st.session_state.pop("_sql_result", None)

if "_sql_result" in st.session_state:
    result = st.session_state["_sql_result"]
    st.caption(f"{len(result):,} row(s) returned")
    st.dataframe(result, use_container_width=True)
    st.download_button("Download as CSV", result.to_csv(index=False).encode("utf-8"),
                        file_name="query_result.csv", mime="text/csv")

saved = repository.recent_queries(sid, limit=10)
if not saved.empty:
    st.divider()
    st.markdown("#### Saved queries")
    for row in saved.itertuples():
        c1, c2 = st.columns([4, 1])
        c1.code(f"{row.name}: {row.sql}", language="sql")
        if c2.button("Load", key=f"load_{row.id}"):
            st.session_state["_prefill_query"] = row.sql
            st.rerun()
