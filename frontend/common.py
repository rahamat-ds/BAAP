"""Shared page-level helpers: dataset guard rails and small UI utilities."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from services import session_service
from visualization.theme import inject_css, page_header


def bootstrap(title: str, subtitle: str = "") -> None:
    """Standard per-page setup: theme CSS + header."""
    inject_css()
    page_header(title)


def require_dataset() -> tuple[str, pd.DataFrame, dict]:
    """Stop the page with a friendly prompt if no dataset is loaded yet.

    Returns (active_name, dataframe, mapping) when a dataset is available.
    """
    if not session_service.has_datasets():
        st.info("No dataset loaded yet. Head to **Upload Center** to load a file or the bundled sample dataset.")
        if st.button("Go generate the sample dataset now", type="primary"):
            from services import dataset_service

            with st.spinner("Generating sample dataset..."):
                dataset_service.load_sample_dataset()
            st.rerun()
        st.stop()

    name = session_service.active_name()
    df = session_service.get_df(name)
    mapping = session_service.get_mapping(name)
    return name, df, mapping


def mapping_hint(missing_roles: list[str]) -> None:
    if missing_roles:
        from config import ROLE_LABELS

        labels = ", ".join(ROLE_LABELS.get(r, r) for r in missing_roles)
        st.caption(f"\u2139\ufe0f Map **{labels}** in Upload Center to unlock this view.")
