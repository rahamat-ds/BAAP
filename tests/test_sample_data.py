"""Tests for services.sample_data_service."""
from __future__ import annotations

import pandas as pd


def test_generate_dataset_shape():
    from services.sample_data_service import generate_dataset

    df = generate_dataset(n_orders=200, seed=1, inject_quality_issues=False)
    assert len(df) == 200
    assert "order_id" in df.columns  # regression test: original generator omitted this
    assert df["order_id"].is_unique


def test_generate_dataset_reproducible():
    from services.sample_data_service import generate_dataset

    a = generate_dataset(n_orders=100, seed=99, inject_quality_issues=False)
    b = generate_dataset(n_orders=100, seed=99, inject_quality_issues=False)
    pd.testing.assert_frame_equal(a, b)


def test_generate_dataset_quality_issues_injected():
    from services.sample_data_service import generate_dataset

    df = generate_dataset(n_orders=2000, seed=5, inject_quality_issues=True)
    assert df.isna().sum().sum() > 0
    assert df.duplicated().sum() > 0


def test_generate_and_save(tmp_path):
    from services.sample_data_service import generate_and_save

    path = tmp_path / "sample.csv"
    df = generate_and_save(path, n_orders=50, seed=3)
    assert path.exists()
    reloaded = pd.read_csv(path)
    assert len(reloaded) == len(df)
