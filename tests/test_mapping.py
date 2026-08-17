"""Tests for core.mapping — the semantic column-role auto-detection engine."""
from __future__ import annotations

import pandas as pd


def test_auto_map_detects_core_roles(clean_sample_df):
    from core.mapping import auto_map

    m = auto_map(clean_sample_df)
    assert m["revenue"] == "revenue"
    assert m["profit"] == "profit"
    assert m["cost"] == "cost"
    assert m["quantity"] == "quantity"
    assert m["date"] == "order_date"
    assert m["customer_id"] == "customer_id"
    assert m["category"] == "category"
    assert m["region"] == "region"


def test_auto_map_generic_dataset():
    from core.mapping import auto_map

    df = pd.DataFrame({
        "Transaction Date": pd.date_range("2024-01-01", periods=10),
        "Total Sales Amount": range(10),
        "Client ID": range(10),
    })
    m = auto_map(df)
    assert m["date"] == "Transaction Date"
    assert m["revenue"] == "Total Sales Amount"
    assert m["customer_id"] == "Client ID"


def test_auto_map_no_false_positive_on_unrelated_columns():
    from core.mapping import auto_map

    df = pd.DataFrame({"random_text": ["a", "b"], "flag": [True, False]})
    m = auto_map(df)
    assert m["revenue"] is None
    assert m["customer_id"] is None


def test_auto_map_retail_roles(clean_sample_df):
    from core.mapping import auto_map, auto_map_retail

    core = auto_map(clean_sample_df)
    used = {v for v in core.values() if v}
    retail_map = auto_map_retail(clean_sample_df, exclude=used)
    assert retail_map["courier"] == "courier"
    assert retail_map["shipping_mode"] == "shipping_mode"
    assert retail_map["rto"] == "rto"


def test_coerce_types(clean_sample_df, mapping):
    from core.mapping import coerce_types

    out = coerce_types(clean_sample_df, mapping)
    assert pd.api.types.is_datetime64_any_dtype(out[mapping["date"]])
    assert pd.api.types.is_numeric_dtype(out[mapping["revenue"]])


def test_mapping_completeness():
    from core.mapping import mapping_completeness

    assert mapping_completeness({"a": "x", "b": None}) == 0.5
    assert mapping_completeness({}) == 0.0
