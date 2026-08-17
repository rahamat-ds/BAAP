"""Tests for pipelines.profiling and pipelines.validation."""
from __future__ import annotations

import pandas as pd


def test_overview_basic(clean_sample_df):
    from pipelines.profiling import overview

    ov = overview(clean_sample_df)
    assert ov.rows == len(clean_sample_df)
    assert ov.columns == clean_sample_df.shape[1]
    assert 0 <= ov.quality_score <= 100


def test_quality_score_penalizes_missing_and_dupes():
    from pipelines.profiling import quality_score

    clean = pd.DataFrame({"a": range(100), "b": range(100)})
    dirty = clean.copy()
    dirty.loc[0:40, "a"] = None
    dirty = pd.concat([dirty, dirty.iloc[:20]], ignore_index=True)

    assert quality_score(clean) > quality_score(dirty)


def test_column_profile_has_expected_columns(clean_sample_df):
    from pipelines.profiling import column_profile

    prof = column_profile(clean_sample_df)
    assert {"Column", "Type", "Nulls", "Unique"}.issubset(prof.columns)
    assert len(prof) == clean_sample_df.shape[1]


def test_correlations_shape(clean_sample_df):
    from pipelines.profiling import correlations

    corr, strong = correlations(clean_sample_df, threshold=0.3)
    assert not corr.empty
    assert "Correlation" in strong.columns or strong.empty


def test_validate_dataset_flags_negative_revenue(mapping):
    from pipelines.validation import validate_dataset

    df = pd.DataFrame({
        mapping["revenue"]: [-100, 200, 300],
        mapping["cost"]: [50, 60, 70],
    })
    partial_mapping = {**{r: None for r in mapping}, "revenue": mapping["revenue"], "cost": mapping["cost"]}
    report = validate_dataset(df, partial_mapping)
    failed_names = {c.name for c in report.failed_checks}
    assert "Negative Revenue" in failed_names


def test_validate_dataset_skips_unmapped_checks():
    from pipelines.validation import validate_dataset

    df = pd.DataFrame({"a": [1, 2, 3]})
    report = validate_dataset(df, {"revenue": None, "profit": None, "cost": None, "quantity": None, "date": None})
    # Only duplicate/missing checks should run; nothing should error out.
    assert len(report.checks) == 2


def test_invalid_rows_selling_below_cost(mapping):
    from pipelines.validation import invalid_rows

    df = pd.DataFrame({mapping["revenue"]: [10, 200], mapping["cost"]: [50, 20]})
    partial_mapping = {"revenue": mapping["revenue"], "cost": mapping["cost"]}
    bad = invalid_rows(df, partial_mapping)
    assert "Selling Below Cost" in bad
    assert len(bad["Selling Below Cost"]) == 1
