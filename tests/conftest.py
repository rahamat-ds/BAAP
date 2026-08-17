"""Shared pytest fixtures."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session")
def sample_df() -> pd.DataFrame:
    """A small, deterministic synthetic retail dataset for fast unit tests."""
    from services.sample_data_service import generate_dataset

    return generate_dataset(n_orders=400, seed=7, inject_quality_issues=True)


@pytest.fixture(scope="session")
def clean_sample_df() -> pd.DataFrame:
    """A quality-issue-free sample for tests that need predictable shapes."""
    from services.sample_data_service import generate_dataset

    return generate_dataset(n_orders=300, seed=11, inject_quality_issues=False)


@pytest.fixture(scope="session")
def mapping(clean_sample_df: pd.DataFrame) -> dict:
    from core.mapping import auto_map

    return auto_map(clean_sample_df)
