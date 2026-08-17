"""Dataset profiling: shape, dtypes, nulls, duplicates, statistics,
correlations, and a 0-100 structural data-quality score.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype

from core.utils import is_text
from models import QualityOverview


def overview(df: pd.DataFrame) -> QualityOverview:
    cells = max(df.shape[0] * df.shape[1], 1)
    ov = QualityOverview(
        rows=len(df),
        columns=df.shape[1],
        duplicate_rows=int(df.duplicated().sum()),
        missing_cells=int(df.isna().sum().sum()),
        missing_pct=float(df.isna().sum().sum() / cells * 100),
        memory_mb=float(df.memory_usage(deep=True).sum() / 1024**2),
        numeric_cols=int(sum(is_numeric_dtype(df[c]) for c in df.columns)),
        text_cols=int(sum(is_text(df[c]) for c in df.columns)),
    )
    ov.quality_score = quality_score(df)
    return ov


def column_profile(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    n = max(len(df), 1)
    for col in df.columns:
        series = df[col]
        nulls = int(series.isna().sum())
        record = {
            "Column": str(col),
            "Type": str(series.dtype),
            "Non-Null": int(series.notna().sum()),
            "Nulls": nulls,
            "Null %": round(nulls / n * 100, 2),
            "Unique": int(series.nunique(dropna=True)),
            "Unique %": round(series.nunique(dropna=True) / n * 100, 2),
            "Memory (KB)": round(series.memory_usage(deep=True) / 1024, 1),
        }
        if is_numeric_dtype(series):
            numeric = pd.to_numeric(series, errors="coerce")
            record.update({
                "Min": round(float(numeric.min()), 2) if numeric.notna().any() else None,
                "Mean": round(float(numeric.mean()), 2) if numeric.notna().any() else None,
                "Max": round(float(numeric.max()), 2) if numeric.notna().any() else None,
                "Std": round(float(numeric.std()), 2) if numeric.notna().any() else None,
            })
            record["Sample"] = ""
        else:
            top = series.dropna().astype(str).value_counts().head(3)
            record["Sample"] = ", ".join(top.index.tolist())
        rows.append(record)
    return pd.DataFrame(rows)


def numeric_stats(df: pd.DataFrame) -> pd.DataFrame:
    numeric = df.select_dtypes(include=np.number)
    if numeric.empty:
        return pd.DataFrame()
    desc = numeric.describe().T
    desc["skew"] = numeric.skew(numeric_only=True)
    desc["kurtosis"] = numeric.kurtosis(numeric_only=True)
    desc["zeros"] = (numeric == 0).sum()
    return desc.round(3)


def correlations(df: pd.DataFrame, threshold: float = 0.5) -> tuple[pd.DataFrame, pd.DataFrame]:
    numeric = df.select_dtypes(include=np.number)
    if numeric.shape[1] < 2:
        return pd.DataFrame(), pd.DataFrame()
    corr = numeric.corr(numeric_only=True).round(3)
    pairs = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool)).stack().reset_index()
    pairs.columns = ["Feature A", "Feature B", "Correlation"]
    pairs["abs"] = pairs["Correlation"].abs()
    strong = (
        pairs[pairs["abs"] >= threshold]
        .sort_values("abs", ascending=False)
        .drop(columns="abs")
        .reset_index(drop=True)
    )
    return corr, strong


def missing_summary(df: pd.DataFrame) -> pd.DataFrame:
    missing = df.isna().sum()
    out = pd.DataFrame({"Column": missing.index.astype(str), "Missing": missing.values})
    out["Missing %"] = (out["Missing"] / max(len(df), 1) * 100).round(2)
    return out[out["Missing"] > 0].sort_values("Missing", ascending=False).reset_index(drop=True)


def quality_score(df: pd.DataFrame) -> int:
    """0-100 heuristic structural data-quality score.

    Penalizes missingness, duplication and near-constant columns. This is
    distinct from :func:`pipelines.validation.validate_dataset`'s
    business-rule score — this one works on *any* dataset with no mapping
    required, while validation checks domain-specific rules once columns
    are mapped.
    """
    ov_cells = max(df.shape[0] * df.shape[1], 1)
    missing_pct = float(df.isna().sum().sum() / ov_cells * 100)
    duplicate_rows = int(df.duplicated().sum())

    score = 100.0
    score -= min(missing_pct * 1.5, 40)
    score -= min(duplicate_rows / max(len(df), 1) * 100 * 1.2, 25)
    constant_cols = sum(df[c].nunique(dropna=False) <= 1 for c in df.columns)
    score -= min(constant_cols / max(df.shape[1], 1) * 100 * 0.3, 15)
    return int(max(0, round(score)))
