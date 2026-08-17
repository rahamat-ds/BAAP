"""Small dtype helpers that behave consistently across pandas versions.

pandas introduced a dedicated string dtype in newer releases, so
``df[col].dtype == object`` is no longer a reliable way to test "is this a
text column" — these helpers centralize the correct check.
"""
from __future__ import annotations

import pandas as pd
from pandas.api.types import (
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_string_dtype,
)


def is_text(series: pd.Series) -> bool:
    """Return True if ``series`` should be treated as free-form text."""
    if is_numeric_dtype(series) or is_datetime64_any_dtype(series):
        return False
    return series.dtype == object or is_string_dtype(series) or str(series.dtype) in ("category", "str")


def text_columns(df: pd.DataFrame) -> list[str]:
    """Return the names of all text-like columns in ``df``."""
    return [c for c in df.columns if is_text(df[c])]


def numeric_columns(df: pd.DataFrame) -> list[str]:
    """Return the names of all numeric columns in ``df``."""
    return [c for c in df.columns if is_numeric_dtype(df[c])]


def datetime_columns(df: pd.DataFrame) -> list[str]:
    """Return the names of all native datetime columns in ``df``."""
    return [c for c in df.columns if is_datetime64_any_dtype(df[c])]


def safe_sample_size(n_rows: int, requested: int) -> int:
    """Clamp a requested sample size to the available number of rows."""
    return max(0, min(requested, n_rows))
