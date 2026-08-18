"""Home — landing page with a quick start and platform overview."""
import streamlit as st

from config import settings
from frontend.common import bootstrap
from services import dataset_service, session_service

bootstrap(settings.app.name, settings.app.tagline)

st.markdown("## Business Analytics Automation Platform")

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("#### 1. Load data")
    st.caption("CSV, Excel, JSON, ZIP, or connect a SQL database. Multiple datasets supported.")
with col2:
    st.markdown("#### 2. Clean & explore")
    st.caption("Auto column-mapping, one-click cleaning, validation, profiling, transformation.")
with col3:
    st.markdown("#### 3. Analyze & report")
    st.caption("KPIs, forecasts, anomalies, AI insights, chat, SQL, and exportable reports.")

st.divider()

if session_service.has_datasets():
    name = session_service.active_name()
    df = session_service.get_df(name)
    st.success(f"Active dataset: **{name}** \u2014 {len(df):,} rows \u00d7 {df.shape[1]} columns")
    nav1, nav2 = st.columns(2)
    with nav1:
        if st.button("Go to Dashboard \u2192", type="primary", use_container_width=True):
            st.switch_page("frontend/pages/dashboard.py")
    with nav2:
        if st.button("Upload another dataset \u2192", use_container_width=True):
            st.switch_page("frontend/pages/upload.py")
else:
    st.info("No dataset loaded yet.")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("\u26a1 Load the sample Indian retail dataset", type="primary", use_container_width=True):
            with st.spinner("Generating a realistic 6,000-order sample dataset..."):
                dataset_service.load_sample_dataset()
            st.rerun()
    with c2:
        if st.button("\u2b06\ufe0f Go to Upload Center", use_container_width=True):
            st.switch_page("frontend/pages/upload.py")

st.divider()
st.markdown("#### What's inside")
features = [
    ("Data Cleaning", "Duplicates, missing values, outliers, text normalization, undo history."),
    ("Profiling & Quality Scoring", "Column-level stats, correlations, a 0-100 structural quality score."),
    ("Business Rule Validation", "Negative revenue, below-cost sales, invalid quantities and more."),
    ("14 Chart Types", "Bar, line, area, pie, treemap, sunburst, waterfall and more, all themed."),
    ("Forecasting", "Ridge regression, Random Forest, or moving-average with confidence bands."),
    ("Anomaly Detection", "Z-score, IQR, Isolation Forest, and rolling time-series anomalies."),
    ("AI Insights & Chat", "Works fully offline; upgrades automatically if you add an LLM API key."),
    ("SQL Workspace", "Query any loaded dataset with real SQL via an in-memory engine."),
    ("Reports", "One-click PDF, Excel and PowerPoint exports with KPIs and AI insights."),
]
cols = st.columns(3)
for i, (title, desc) in enumerate(features):
    with cols[i % 3]:
        st.markdown(f"**{title}**")
        st.caption(desc)
