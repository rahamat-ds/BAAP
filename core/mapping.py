"""Auto-detection of semantic column roles.

This is the piece of engineering that makes InsightFlow work on *any*
tabular dataset rather than only the bundled Indian-retail sample: every
analytics, forecasting and chat module reads a *role* (``revenue``,
``date``, ``customer_id`` ...) instead of a hard-coded column name. Roles
are auto-detected from header text and dtype, then are fully editable by
the user in the Upload Center / Settings page.
"""
from __future__ import annotations

import re

import pandas as pd
from pandas.api.types import is_bool_dtype, is_datetime64_any_dtype, is_numeric_dtype

from config import ROLE_PATTERNS, ROLES
from core.logging_config import get_logger
from core.utils import is_text

logger = get_logger(__name__)


def _is_dateish(series: pd.Series) -> bool:
    """Heuristically decide whether a column represents dates."""
    if is_datetime64_any_dtype(series):
        return True
    if is_text(series):
        sample = series.dropna().astype(str).head(40)
        if sample.empty:
            return False
        parsed_ratio = pd.to_datetime(sample, errors="coerce", format="mixed").notna().mean()
        return parsed_ratio > 0.8
    return False


def _score(df: pd.DataFrame, role: str, column, patterns: dict[str, str], all_roles: list[str]) -> int:
    """Score how well ``column`` fits ``role``. Higher is better; 0 = no fit."""
    name = str(column).lower().strip()
    match = re.search(patterns[role], name)
    if not match:
        return 0
    if role in ("revenue", "profit", "cost", "quantity", "delivery_days", "discount"):
        if not is_numeric_dtype(df[column]) or is_bool_dtype(df[column]):
            return 0
    if role == "date" and not _is_dateish(df[column]):
        return 0

    name_norm = re.sub(r"[^a-z0-9]", "", name)
    token = re.sub(r"[^a-z0-9]", "", match.group(0))
    base = 10
    if name_norm in (token, token + "s"):
        base = 40
    elif name_norm.startswith(token):
        base = 30
    elif name_norm.endswith(token):
        base = 20

    # A column literally named after the role itself (e.g. a "region" column
    # for the "region" role) is an unambiguous, exact signal — it should
    # always outrank a same-tier synonym match (e.g. a "state" column also
    # matching the "region" role's pattern).
    role_token = re.sub(r"[^a-z0-9]", "", role)
    if name_norm == role_token:
        base += 20

    # A column whose name also matches a different, more specific role loses
    # points so ambiguous headers (e.g. "cost" vs "cost_center") settle on
    # the best-fit role rather than the first one checked.
    for other in all_roles:
        if other != role and re.search(patterns[other], name):
            base -= 4
    return base


def _auto_map_generic(
    df: pd.DataFrame, roles: list[str], patterns: dict[str, str], used: set
) -> dict[str, str | None]:
    mapping: dict[str, str | None] = {r: None for r in roles}
    for role in roles:
        candidates = [(_score(df, role, c, patterns, roles), c) for c in df.columns if c not in used]
        candidates = [(score, c) for score, c in candidates if score > 0]
        if candidates:
            best = max(candidates, key=lambda t: t[0])[1]
            mapping[role] = best
            used.add(best)
    return mapping


def auto_map(df: pd.DataFrame) -> dict[str, str | None]:
    """Best-effort mapping of dataframe columns onto the core semantic roles."""
    used: set = set()
    mapping = _auto_map_generic(df, ROLES, ROLE_PATTERNS, used)

    # Fallbacks so the dashboard is never empty on a "normal" business dataset.
    if mapping["date"] is None:
        for c in df.columns:
            if c not in used and _is_dateish(df[c]):
                mapping["date"] = c
                used.add(c)
                break
    if mapping["revenue"] is None:
        numeric_cols = [
            c for c in df.columns
            if is_numeric_dtype(df[c]) and not is_bool_dtype(df[c]) and c not in used
        ]
        if numeric_cols:
            best = max(numeric_cols, key=lambda c: float(pd.to_numeric(df[c], errors="coerce").abs().sum()))
            mapping["revenue"] = best
            used.add(best)

    logger.debug("Auto-mapped columns: %s", {k: v for k, v in mapping.items() if v})
    return mapping


def auto_map_retail(df: pd.DataFrame, exclude: set | None = None) -> dict[str, str | None]:
    """Best-effort mapping onto the *optional* retail-operations roles.

    Used only by the Retail Operations module; datasets without a match
    simply don't surface that module's content.
    """
    from config import RETAIL_ROLE_PATTERNS, RETAIL_ROLES

    used = set(exclude or set())
    return _auto_map_generic(df, RETAIL_ROLES, RETAIL_ROLE_PATTERNS, used)


def coerce_types(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    """Return a copy of ``df`` with mapped date/numeric columns coerced."""
    out = df.copy()
    date_col = mapping.get("date")
    if date_col and date_col in out.columns and not is_datetime64_any_dtype(out[date_col]):
        out[date_col] = pd.to_datetime(out[date_col], errors="coerce", format="mixed")
    for role in ("revenue", "profit", "cost", "quantity", "delivery_days", "discount"):
        col = mapping.get(role)
        if col and col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def mapping_completeness(mapping: dict) -> float:
    """Return the fraction (0-1) of roles that were successfully mapped."""
    if not mapping:
        return 0.0
    filled = sum(1 for v in mapping.values() if v)
    return filled / len(mapping)
