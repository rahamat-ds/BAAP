"""Export Data — download the active (or any loaded) dataset in common formats."""
import streamlit as st

from frontend.common import bootstrap
from services import report_service, session_service

bootstrap("Export Data", "Download any loaded dataset as CSV, Excel or JSON.")

names = session_service.dataset_names()
if not names:
    st.info("No datasets loaded yet. Head to Upload Center first.")
    st.stop()

target = st.selectbox("Dataset", names, index=names.index(session_service.active_name()))
df = session_service.get_df(target)
st.caption(f"{len(df):,} rows \u00d7 {df.shape[1]} columns")

use_all_rows = st.checkbox("Export all rows", value=True)
n_rows = len(df) if use_all_rows else st.slider("Rows to export", 10, min(len(df), 10_000), min(1000, len(df)))
export_df = df.head(n_rows)

st.dataframe(export_df.head(20), use_container_width=True)

c1, c2, c3 = st.columns(3)
with c1:
    st.download_button("\u2b07\ufe0f CSV", report_service.build_csv(export_df), file_name=f"{target}.csv",
                        mime="text/csv", use_container_width=True)
with c2:
    excel_bytes = report_service.build_excel({target: export_df})
    st.download_button("\u2b07\ufe0f Excel", excel_bytes, file_name=f"{target}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True)
with c3:
    st.download_button("\u2b07\ufe0f JSON", export_df.to_json(orient="records", indent=2).encode("utf-8"),
                        file_name=f"{target}.json", mime="application/json", use_container_width=True)
