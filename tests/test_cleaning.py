"""Tests for pipelines.cleaning."""
from __future__ import annotations

import numpy as np
import pandas as pd


def test_remove_duplicates():
    from pipelines.cleaning import remove_duplicates

    df = pd.DataFrame({"a": [1, 1, 2], "b": [1, 1, 2]})
    out, msg = remove_duplicates(df)
    assert len(out) == 2
    assert "1" in msg


def test_handle_missing_mean():
    from pipelines.cleaning import handle_missing

    df = pd.DataFrame({"x": [1.0, np.nan, 3.0]})
    out, _ = handle_missing(df, strategy="mean", columns=["x"])
    assert out["x"].isna().sum() == 0
    assert out["x"].iloc[1] == 2.0


def test_handle_missing_drop_rows():
    from pipelines.cleaning import handle_missing

    df = pd.DataFrame({"x": [1, None, 3]})
    out, _ = handle_missing(df, strategy="drop_rows", columns=["x"])
    assert len(out) == 2


def test_trim_whitespace():
    from pipelines.cleaning import trim_whitespace

    df = pd.DataFrame({"name": ["  Alice  ", "Bob   Smith"]})
    out, _ = trim_whitespace(df, columns=["name"])
    assert out["name"].iloc[0] == "Alice"
    assert out["name"].iloc[1] == "Bob Smith"


def test_remove_outliers_iqr():
    from pipelines.cleaning import remove_outliers

    df = pd.DataFrame({"v": [10, 11, 12, 13, 1000]})
    out, _ = remove_outliers(df, ["v"], method="iqr", factor=1.5, action="remove")
    assert 1000 not in out["v"].values


def test_convert_types():
    from pipelines.cleaning import convert_types

    df = pd.DataFrame({"x": ["1", "2", "3"]})
    out, _ = convert_types(df, "x", "integer")
    assert str(out["x"].dtype).startswith("Int")


def test_clean_column_names():
    from pipelines.cleaning import clean_column_names

    df = pd.DataFrame({"First Name!!": [1], "  Weird Col ": [2]})
    out, _ = clean_column_names(df)
    assert list(out.columns) == ["first_name", "weird_col"]


def test_auto_clean_reduces_missing_and_dupes(sample_df):
    from pipelines.cleaning import auto_clean

    out, report = auto_clean(sample_df)
    assert report["rows_before"] == len(sample_df)
    assert out.isna().sum().sum() <= sample_df.isna().sum().sum()
    assert out.duplicated().sum() == 0
