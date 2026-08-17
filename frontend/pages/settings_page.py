"""Settings — LLM provider status, app preferences, and session controls."""
import streamlit as st

import llm
from config import settings
from frontend.common import bootstrap
from services import session_service

bootstrap("Settings", "Configure AI providers and manage your session.")

tab_ai, tab_prefs, tab_session = st.tabs(["\U0001f916 AI Provider", "\u2699\ufe0f Preferences", "\U0001f5c2\ufe0f Session"])

with tab_ai:
    st.markdown("InsightFlow's AI Insights and Chat-with-Data features work **fully offline** using deterministic, "
                "rule-based analysis. Configure an API key below to upgrade them with natural-language generation.")
    st.caption("API keys are read from environment variables (or a local `.env` file) and are never sent anywhere "
               "except directly to the provider you choose.")

    current = llm.active_provider_name()
    if current:
        st.success(f"Active provider: **{current.title()}**")
    else:
        st.warning("No AI provider configured \u2014 running in offline mode.")

    st.code(
        "# In your .env file, set ONE of:\n"
        "ANTHROPIC_API_KEY=sk-ant-...\n"
        "OPENAI_API_KEY=sk-...\n"
        "GEMINI_API_KEY=...\n\n"
        "# Optionally force a specific provider (default: auto)\n"
        "LLM_PROVIDER=anthropic",
        language="bash",
    )
    st.caption("Restart the app after editing `.env` for changes to take effect.")

with tab_prefs:
    st.markdown(f"**App:** {settings.app.name} v{settings.app.version}")
    st.markdown(f"**Currency symbol:** `{settings.currency_symbol}` (set via `APP_CURRENCY` env var)")
    st.markdown(f"**Revenue target:** {settings.currency_symbol}{settings.revenue_target:,.0f} (set via `APP_TARGET_REVENUE`)")
    st.markdown(f"**Max upload size:** {settings.max_upload_mb} MB (set via `MAX_UPLOAD_MB`)")
    st.caption("Preferences are configured via environment variables — see `.env.example` and `docs/CONFIGURATION.md`.")

with tab_session:
    names = session_service.dataset_names()
    st.markdown(f"**Datasets loaded this session:** {len(names)}")
    for n in names:
        st.caption(f"\u2022 {n}")

    st.divider()
    st.markdown("#### Reset")
    if st.button("Clear all loaded datasets", type="secondary"):
        session_service.clear_all()
        st.success("All datasets cleared.")
        st.rerun()
