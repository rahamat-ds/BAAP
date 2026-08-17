"""Tests for forecasting.models and forecasting.anomalies."""
from __future__ import annotations

import pandas as pd
import pytest


def test_forecast_ridge(clean_sample_df, mapping):
    from forecasting.models import forecast

    result_df, metrics = forecast(clean_sample_df, mapping, periods=14, freq="D", method="ridge")
    assert not result_df.empty
    assert {"date", "actual", "forecast", "lower", "upper"}.issubset(result_df.columns)
    assert result_df["forecast"].notna().sum() == 14
    assert metrics.forecast_total is not None


def test_forecast_moving_average(clean_sample_df, mapping):
    from forecasting.models import forecast

    result_df, metrics = forecast(clean_sample_df, mapping, periods=7, freq="D", method="moving_average")
    assert result_df["forecast"].notna().sum() == 7


def test_forecast_random_forest(clean_sample_df, mapping):
    from forecasting.models import forecast

    result_df, metrics = forecast(clean_sample_df, mapping, periods=7, freq="D", method="random_forest")
    assert result_df["forecast"].notna().sum() == 7
    assert (result_df["forecast"].dropna() >= 0).all()


def test_forecast_requires_date_and_revenue(clean_sample_df):
    from forecasting.models import forecast

    with pytest.raises(ValueError):
        forecast(clean_sample_df, {"date": None, "revenue": None}, periods=7)


def test_detect_zscore():
    from forecasting.anomalies import detect_zscore

    df = pd.DataFrame({"v": [1, 2, 3, 2, 1, 1000]})
    out = detect_zscore(df, "v", threshold=2.0)
    assert 1000 in out["v"].values


def test_detect_iqr():
    from forecasting.anomalies import detect_iqr

    df = pd.DataFrame({"v": [10, 11, 12, 13, 14, 500]})
    out = detect_iqr(df, "v")
    assert 500 in out["v"].values


def test_detect_isolation_forest():
    from forecasting.anomalies import detect_isolation_forest

    df = pd.DataFrame({"a": list(range(50)) + [500], "b": list(range(50)) + [-500]})
    out = detect_isolation_forest(df, ["a", "b"], contamination=0.05)
    assert len(out) >= 1


def test_time_series_anomalies(clean_sample_df, mapping):
    from forecasting.anomalies import detect_time_series_anomalies

    result = detect_time_series_anomalies(clean_sample_df, mapping, threshold=2.0)
    assert isinstance(result, pd.DataFrame)
