"""Data transformation operations: reshaping, feature engineering, merges.

Distinct from :mod:`pipelines.cleaning` — these operations reshape or
enrich data rather than fix quality issues.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def group_and_aggregate(df: pd.DataFrame, group_cols: list[str], agg_map: dict[str, str]) -> pd.DataFrame:
    """Group by ``group_cols`` and aggregate ``{column: agg_fn}`` pairs."""
    grouped = df.groupby(group_cols, dropna=False).agg(agg_map)
    grouped.columns = [f"{col}_{fn}" for col, fn in agg_map.items()]
    return grouped.reset_index()


def pivot(df: pd.DataFrame, index: str, columns: str, values: str, aggfunc: str = "sum") -> pd.DataFrame:
    table = pd.pivot_table(df, index=index, columns=columns, values=values, aggfunc=aggfunc, fill_value=0)
    table.columns = [str(c) for c in table.columns]
    return table.reset_index()


def merge_datasets(left: pd.DataFrame, right: pd.DataFrame, on: list[str] | str, how: str = "inner") -> pd.DataFrame:
    return left.merge(right, on=on, how=how)


def split_column(df: pd.DataFrame, column: str, delimiter: str = " ", new_names: list[str] | None = None):
    out = df.copy()
    parts = out[column].astype(str).str.split(delimiter, expand=True)
    names = new_names or [f"{column}_{i+1}" for i in range(parts.shape[1])]
    parts.columns = names[: parts.shape[1]]
    return pd.concat([out, parts], axis=1)


def add_date_parts(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
    out = df.copy()
    parsed = pd.to_datetime(out[date_col], errors="coerce")
    out[f"{date_col}_year"] = parsed.dt.year
    out[f"{date_col}_month"] = parsed.dt.month
    out[f"{date_col}_month_name"] = parsed.dt.month_name()
    out[f"{date_col}_quarter"] = parsed.dt.quarter
    out[f"{date_col}_weekday"] = parsed.dt.day_name()
    out[f"{date_col}_is_weekend"] = parsed.dt.dayofweek.isin([5, 6])
    return out


def bin_column(df: pd.DataFrame, column: str, bins: int = 5, labels: list[str] | None = None) -> pd.DataFrame:
    out = df.copy()
    out[f"{column}_bin"] = pd.cut(pd.to_numeric(out[column], errors="coerce"), bins=bins, labels=labels)
    return out


def normalize_column(df: pd.DataFrame, column: str, method: str = "minmax") -> pd.DataFrame:
    out = df.copy()
    series = pd.to_numeric(out[column], errors="coerce")
    if method == "zscore":
        out[f"{column}_norm"] = (series - series.mean()) / (series.std() or 1)
    else:
        span = (series.max() - series.min()) or 1
        out[f"{column}_norm"] = (series - series.min()) / span
    return out


def create_calculated_column(df: pd.DataFrame, name: str, expression: str) -> pd.DataFrame:
    """Create a new column from a pandas ``eval`` expression over existing columns.

    Expression is evaluated with pandas' ``eval`` in a restricted local
    namespace (no builtins, only the dataframe's own columns and numpy),
    e.g. ``"revenue - cost"``.
    """
    out = df.copy()
    out[name] = out.eval(expression, engine="python", local_dict={"np": np})
    return out


def encode_categorical(df: pd.DataFrame, column: str, method: str = "onehot") -> pd.DataFrame:
    out = df.copy()
    if method == "onehot":
        dummies = pd.get_dummies(out[column], prefix=column)
        return pd.concat([out, dummies], axis=1)
    codes, _ = pd.factorize(out[column])
    out[f"{column}_encoded"] = codes
    return out
