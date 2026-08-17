"""AI Insights — AI-generated (or rule-based offline) business insights."""
import streamlit as st

import llm
from analytics.insights import generate_insights
from frontend.common import bootstrap, require_dataset
from visualization.theme import insight_card

bootstrap("AI Insights", "Automated business insights \u2014 upgrades automatically if an LLM key is configured.")

name, df, mapping = require_dataset()

if llm.is_available():
    st.caption(f"\U0001f7e2 Using **{llm.active_provider_name().title()}** for AI-generated insights.")
else:
    st.caption("\u26aa Running in offline analyst mode (rule-based). Add an API key in Settings to enable AI narration.")

if st.button("\u2728 Generate insights", type="primary"):
    with st.spinner("Analyzing your data..."):
        insight_list, source = generate_insights(df, mapping)
    st.session_state["_last_insights"] = (insight_list, source)

if "_last_insights" in st.session_state:
    insight_list, source = st.session_state["_last_insights"]
    st.caption(f"Source: {'AI-generated' if source == 'ai' else 'Rule-based (offline)'}")
    for text in insight_list:
        insight_card(text.replace("\n", "<br/>"))
else:
    st.info("Click **Generate insights** to analyze the active dataset.")
