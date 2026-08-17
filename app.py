"""InsightFlow — Business Analytics Automation Platform.

Run with:  streamlit run app.py
"""
from __future__ import annotations

import streamlit as st

import llm
from config import settings
from database import engine as db_engine
from services import session_service
from visualization.theme import inject_css

st.set_page_config(
    page_title=settings.app.name,
    page_icon=settings.app.icon,
    layout="wide",
    initial_sidebar_state="expanded",
)

db_engine()  # ensure schema exists
session_service.session_id()  # ensure session state initialized
inject_css()

PAGES = {
    "Overview": [
        st.Page("frontend/pages/home.py", title="Home", default=True),
        st.Page("frontend/pages/dashboard.py", title="Dashboard"),
    ],
    "Data": [
        st.Page("frontend/pages/upload.py", title="Upload Center"),
        st.Page("frontend/pages/profiling.py", title="Data Profiling"),
        st.Page("frontend/pages/cleaning.py", title="Data Cleaning"),
        st.Page("frontend/pages/validation.py", title="Data Validation"),
        st.Page("frontend/pages/transform.py", title="Transformation"),
    ],
    "Analytics": [
        st.Page("frontend/pages/analytics_explorer.py", title="Analytics"),
        st.Page("frontend/pages/visualizations.py", title="Visualizations"),
        st.Page("frontend/pages/customers.py", title="Customer Analytics" ),
        st.Page("frontend/pages/products.py", title="Product Analytics"),
        st.Page("frontend/pages/retail_ops.py", title="Retail Operations"),
        st.Page("frontend/pages/forecasting_page.py", title="Forecasting"),
        st.Page("frontend/pages/anomalies.py", title="Anomaly Detection"),
    ],
    "AI": [
        st.Page("frontend/pages/insights.py", title="AI Insights"),
        st.Page("frontend/pages/chat_page.py", title="Chat with Data"),
    ],
    "Tools": [
        st.Page("frontend/pages/sql_workspace.py", title="SQL Workspace"),
        st.Page("frontend/pages/reports.py", title="Reports"),
        st.Page("frontend/pages/exports.py", title="Export Data"),
    ],
    "System": [
        st.Page("frontend/pages/history.py", title="History"),
        st.Page("frontend/pages/settings_page.py", title="Settings"),
    ],
}

with st.sidebar:
    st.markdown(
        f"<div style='display:flex;align-items:center;gap:10px;padding:2px 0 10px'>"
        f"<div style='font-size:26px'>{settings.app.icon}</div>"
        f"<div><div style='font-weight:700;line-height:1.15;font-size:1.05rem'>{settings.app.name}</div>"
        f"<div style='font-size:0.72rem;color:#9095A8'>{settings.app.tagline}</div></div></div>",
        unsafe_allow_html=True,
    )

nav = st.navigation(PAGES, position="sidebar")

with st.sidebar:
    st.divider()
    st.caption("ACTIVE DATASET")
    names = session_service.dataset_names()
    if names:
        current = session_service.active_name()
        choice = st.selectbox("Active dataset", names, index=names.index(current) if current in names else 0,
                               label_visibility="collapsed")
        if choice != current:
            session_service.set_active(choice)
            st.rerun()
        df = session_service.get_df(choice)
        st.caption(f"{len(df):,} rows \u00d7 {df.shape[1]} cols")
    else:
        st.caption("None loaded")
        if st.button("\u26a1 Load demo data", use_container_width=True):
            from services import dataset_service

            with st.spinner("Generating sample dataset..."):
                dataset_service.load_sample_dataset()
            st.rerun()

    st.divider()
    provider = llm.active_provider_name()
    st.caption(f"\U0001f7e2 {provider.title()} connected" if provider else "\u26aa Offline analyst mode")
    st.caption(f"v{settings.app.version}")

nav.run()
