"""End-to-end smoke test: renders every page via Streamlit's AppTest harness
with a real dataset pre-loaded in session state, asserting no uncaught
exceptions. This is what actually catches broken imports, bad Streamlit API
usage, and wiring mistakes that unit tests on pure functions can't see.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent.parent
PAGES_DIR = ROOT / "frontend" / "pages"

ALL_PAGES = sorted(p.name for p in PAGES_DIR.glob("*.py"))


def _preload_session_state(at: AppTest) -> None:
    """Inject a loaded dataset directly into session state before running,
    mirroring what services.session_service.register_dataset does, so pages
    that require an active dataset exercise their real content path.
    """
    from services.sample_data_service import generate_dataset
    from services.session_service import _AppState, _DatasetEntry
    from core.mapping import auto_map

    df = generate_dataset(n_orders=250, seed=42, inject_quality_issues=True)
    entry = _DatasetEntry(df=df, source="test", mapping=auto_map(df))
    state = _AppState(session_id="test-session", datasets={"Indian_Retail_Orders": entry}, active="Indian_Retail_Orders")
    at.session_state["_insightflow_state"] = state


@pytest.mark.parametrize("page_name", ALL_PAGES)
def test_page_renders_without_dataset(page_name: str):
    """Every page should degrade gracefully (no crash) with zero data loaded."""
    at = AppTest.from_file(str(PAGES_DIR / page_name), default_timeout=30)
    at.run()
    assert not at.exception, f"{page_name} raised: {[str(e) for e in at.exception]}"


@pytest.mark.parametrize("page_name", ALL_PAGES)
def test_page_renders_with_dataset(page_name: str):
    """Every page should render its real content path with a dataset loaded."""
    at = AppTest.from_file(str(PAGES_DIR / page_name), default_timeout=30)
    _preload_session_state(at)
    at.run()
    assert not at.exception, f"{page_name} raised: {[str(e) for e in at.exception]}"
