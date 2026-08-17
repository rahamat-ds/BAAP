"""History — session management: activity log, datasets loaded, reports, chat, queries."""
import streamlit as st

from database import repository
from frontend.common import bootstrap
from services import session_service

bootstrap("History", "A record of what's happened in this and past sessions.")

sid = session_service.session_id()
scope = st.radio("Scope", ["This session", "All time"], horizontal=True)
filter_sid = sid if scope == "This session" else None

tab_activity, tab_datasets, tab_reports, tab_chat = st.tabs(["Activity Log", "Datasets Loaded", "Reports Generated", "Chat Transcripts"])

with tab_activity:
    activity = repository.recent_activity(filter_sid, limit=100)
    if activity.empty:
        st.caption("No activity recorded yet.")
    else:
        st.dataframe(activity[["created_at", "action", "detail"]], use_container_width=True, hide_index=True)

with tab_datasets:
    datasets = repository.recent_datasets(filter_sid, limit=100)
    if datasets.empty:
        st.caption("No datasets logged yet.")
    else:
        st.dataframe(datasets[["created_at", "name", "source", "rows", "cols"]], use_container_width=True, hide_index=True)

with tab_reports:
    reports = repository.recent_reports(filter_sid, limit=100)
    if reports.empty:
        st.caption("No reports generated yet.")
    else:
        st.dataframe(reports[["created_at", "name", "kind"]], use_container_width=True, hide_index=True)

with tab_chat:
    chat = repository.recent_chat(filter_sid, limit=200)
    if chat.empty:
        st.caption("No chat history yet.")
    else:
        st.dataframe(chat[["created_at", "dataset", "role", "message"]], use_container_width=True, hide_index=True)

st.divider()
if st.button("\U0001f5d1\ufe0f Clear this session's history", type="secondary"):
    repository.clear_session(sid)
    st.success("Session history cleared.")
    st.rerun()
