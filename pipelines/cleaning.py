"""One-click data cleaning operations.

Every function takes a DataFrame (and operation-specific arguments) and
returns ``(new_df, human_readable_message)`` so the calling page can apply
the result and show what happened in one line — and log it to the
in-session cleaning history for one-click undo.
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype

from core.utils import text_columns


def remove_duplicates(df: pd.DataFrame, subset: list[str] | None = None, keep: str = "first"):
    before = len(df)
    out = df.drop_duplicates(subset=subset or None, keep=keep)
    return out.reset_index(drop=True), f"Removed {before - len(out):,} duplicate rows."


def handle_missing(df: pd.DataFrame, strategy: str = "drop_rows", columns: list[str] | None = None,
                    fill_value=None):
    cols = columns or list(df.columns)
    out = df.copy()

    if strategy == "drop_rows":
        before = len(out)
        out = out.dropna(subset=cols).reset_index(drop=True)
        return out, f"Dropped {before - len(out):,} rows containing nulls."

    if strategy == "drop_columns":
        drop = [c for c in cols if out[c].isna().any()]
        return out.drop(columns=drop), f"Dropped {len(drop)} column(s) with nulls."

    filled = 0
    for col in cols:
        n_missing = int(out[col].isna().sum())
        if not n_missing:
            continue
        if strategy == "mean" and is_numeric_dtype(out[col]):
            out[col] = out[col].fillna(out[col].mean())
        elif strategy == "median" and is_numeric_dtype(out[col]):
            out[col] = out[col].fillna(out[col].median())
        elif strategy == "mode":
            mode = out[col].mode()
            if not mode.empty:
                out[col] = out[col].fillna(mode.iloc[0])
        elif strategy == "zero" and is_numeric_dtype(out[col]):
            out[col] = out[col].fillna(0)
        elif strategy == "ffill":
            out[col] = out[col].ffill()
        elif strategy == "bfill":
            out[col] = out[col].bfill()
        elif strategy == "constant":
            out[col] = out[col].fillna(fill_value)
        else:
            continue
        filled += n_missing
    return out, f"Imputed {filled:,} missing values using '{strategy}'."


def standardize_dates(df: pd.DataFrame, columns: list[str], output: str = "datetime", fmt: str = "%Y-%m-%d"):
    out = df.copy()
    done = []
    for col in columns:
        parsed = pd.to_datetime(out[col], errors="coerce", format="mixed")
        out[col] = parsed.dt.strftime(fmt) if output == "string" else parsed
        done.append(str(col))
    return out, f"Standardized date column(s): {', '.join(done)}."


def fix_text_case(df: pd.DataFrame, columns: list[str], mode: str = "title"):
    out = df.copy()
    fn = {"lower": str.lower, "upper": str.upper, "title": str.title, "capitalize": str.capitalize}[mode]
    for col in columns:
        out[col] = out[col].astype(str).map(lambda v: fn(v) if v not in ("nan", "None") else np.nan)
    return out, f"Applied '{mode}' case to {len(columns)} column(s)."


def trim_whitespace(df: pd.DataFrame, columns: list[str] | None = None):
    out = df.copy()
    cols = columns or text_columns(out)
    for col in cols:
        out[col] = out[col].astype(str).str.strip().replace({"nan": np.nan, "None": np.nan})
        out[col] = out[col].astype(str).str.replace(r"\s+", " ", regex=True).replace({"nan": np.nan})
    return out, f"Trimmed whitespace in {len(cols)} column(s)."


def remove_outliers(df: pd.DataFrame, columns: list[str], method: str = "iqr", factor: float = 1.5,
                     action: str = "remove"):
    out = df.copy()
    mask = pd.Series(False, index=out.index)
    for col in columns:
        series = pd.to_numeric(out[col], errors="coerce")
        if method == "iqr":
            q1, q3 = series.quantile(0.25), series.quantile(0.75)
            iqr = q3 - q1
            lo, hi = q1 - factor * iqr, q3 + factor * iqr
        else:  # z-score
            lo, hi = series.mean() - factor * series.std(), series.mean() + factor * series.std()
        bad = (series < lo) | (series > hi)
        if action == "clip":
            out[col] = series.clip(lo, hi)
        else:
            mask |= bad.fillna(False)
    if action == "clip":
        return out, f"Clipped outliers in {len(columns)} column(s) ({method})."
    n = int(mask.sum())
    return out[~mask].reset_index(drop=True), f"Removed {n:,} outlier rows ({method}, factor {factor})."


def rename_columns(df: pd.DataFrame, mapping: dict):
    mapping = {k: v for k, v in mapping.items() if v and v != k}
    return df.rename(columns=mapping), f"Renamed {len(mapping)} column(s)."


def clean_column_names(df: pd.DataFrame):
    def norm(col):
        col = re.sub(r"[^0-9a-zA-Z]+", "_", str(col)).strip("_").lower()
        return col or "col"

    return df.rename(columns={c: norm(c) for c in df.columns}), "Normalized all column names to snake_case."


def convert_types(df: pd.DataFrame, column: str, target: str):
    out = df.copy()
    if target == "numeric":
        out[column] = pd.to_numeric(out[column], errors="coerce")
    elif target == "integer":
        out[column] = pd.to_numeric(out[column], errors="coerce").astype("Int64")
    elif target == "datetime":
        out[column] = pd.to_datetime(out[column], errors="coerce", format="mixed")
    elif target == "string":
        out[column] = out[column].astype(str)
    elif target == "category":
        out[column] = out[column].astype("category")
    elif target == "boolean":
        out[column] = out[column].astype(str).str.lower().isin(["1", "true", "yes", "y", "t"])
    return out, f"Converted '{column}' to {target}."


def drop_columns(df: pd.DataFrame, columns: list[str]):
    return df.drop(columns=list(columns)), f"Dropped {len(columns)} column(s)."


def auto_clean(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """One-click pipeline: dedupe -> trim text -> fill missing sensibly.

    Returns the cleaned frame plus a small report dict for display, mirroring
    the original InsightFlow "Clean Dataset" button behaviour.
    """
    report: dict[str, int] = {"rows_before": len(df)}

    out, _ = remove_duplicates(df)
    report["duplicates_removed"] = report["rows_before"] - len(out)

    out, _ = trim_whitespace(out)

    before_missing = int(out.isna().sum().sum())
    out, _ = handle_missing(out, strategy="median", columns=out.select_dtypes(include=np.number).columns.tolist())
    out, _ = handle_missing(out, strategy="mode", columns=text_columns(out))
    after_missing = int(out.isna().sum().sum())
    report["missing_values_filled"] = before_missing - after_missing
    report["rows_after"] = len(out)
    return out, report
