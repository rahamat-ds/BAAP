"""Time-series forecasting.

Offers three interchangeable methods so users can trade off simplicity vs
accuracy: a moving-average baseline, linear (Ridge) regression on a time
index plus seasonal features, and a Random Forest regressor for non-linear
trends. All three share a common output contract so the UI layer doesn't
need to know which one ran.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from models import ForecastMetrics


def _prepare_series(df: pd.DataFrame, mapping: dict, freq: str = "D") -> pd.Series:
    date_c, revenue_c = mapping.get("date"), mapping.get("revenue")
    if not date_c or not revenue_c:
        raise ValueError("Forecasting requires both a 'date' and 'revenue' column to be mapped.")
    parsed = pd.to_datetime(df[date_c], errors="coerce")
    values = pd.to_numeric(df[revenue_c], errors="coerce")
    series = (
        pd.DataFrame({"date": parsed, "value": values})
        .dropna(subset=["date"])
        .groupby("date")["value"].sum()
        .asfreq(freq, fill_value=0)
        .sort_index()
    )
    return series


def _feature_frame(index: pd.DatetimeIndex) -> pd.DataFrame:
    t = np.arange(len(index))
    return pd.DataFrame({
        "t": t,
        "dow": index.dayofweek,
        "month": index.month,
        "doy_sin": np.sin(2 * np.pi * index.dayofyear / 365.25),
        "doy_cos": np.cos(2 * np.pi * index.dayofyear / 365.25),
    })


def forecast(
    df: pd.DataFrame,
    mapping: dict,
    periods: int = 30,
    freq: str = "D",
    method: str = "ridge",
) -> tuple[pd.DataFrame, ForecastMetrics]:
    """Forecast the mapped revenue metric ``periods`` steps into the future.

    Returns a tidy frame with columns ``date, actual, forecast, lower, upper``
    (actual is NaN for future rows, forecast/lower/upper are NaN for
    historical rows) plus diagnostic metrics computed via a holdout split.
    """
    series = _prepare_series(df, mapping, freq)
    if len(series) < 10:
        raise ValueError("Need at least 10 historical periods with data to forecast.")

    if method == "moving_average":
        return _forecast_moving_average(series, periods, freq)
    if method == "random_forest":
        return _forecast_ml(series, periods, freq, model="rf")
    return _forecast_ml(series, periods, freq, model="ridge")


def _holdout_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> tuple[float, float]:
    mae = float(np.mean(np.abs(y_true - y_pred)))
    nonzero = y_true != 0
    mape = float(np.mean(np.abs((y_true[nonzero] - y_pred[nonzero]) / y_true[nonzero])) * 100) if nonzero.any() else float("nan")
    return mae, mape


def _forecast_moving_average(series: pd.Series, periods: int, freq: str) -> tuple[pd.DataFrame, ForecastMetrics]:
    window = max(3, min(14, len(series) // 4))
    rolling = series.rolling(window).mean()

    holdout = min(periods, max(1, len(series) // 5))
    mae, mape = _holdout_metrics(series.values[-holdout:], rolling.values[-holdout:]) if holdout else (None, None)

    last_avg = float(series.tail(window).mean())
    trend = float((series.tail(window).mean() - series.head(window).mean()) / max(len(series), 1))
    future_idx = pd.date_range(series.index[-1], periods=periods + 1, freq=freq)[1:]
    future_vals = [max(0.0, last_avg + trend * i) for i in range(1, periods + 1)]
    std = float(series.tail(window).std() or 0)

    hist = pd.DataFrame({"date": series.index, "actual": series.values, "forecast": np.nan, "lower": np.nan, "upper": np.nan})
    fut = pd.DataFrame({
        "date": future_idx, "actual": np.nan, "forecast": future_vals,
        "lower": [max(0.0, v - 1.28 * std) for v in future_vals],
        "upper": [v + 1.28 * std for v in future_vals],
    })
    out = pd.concat([hist, fut], ignore_index=True)
    metrics = ForecastMetrics(
        mae=mae, mape_pct=mape, historical_total=float(series.sum()), forecast_total=float(sum(future_vals)),
        expected_growth_pct=float((sum(future_vals) / periods - last_avg) / max(last_avg, 1e-9) * 100),
    )
    return out, metrics


def _forecast_ml(series: pd.Series, periods: int, freq: str, model: str) -> tuple[pd.DataFrame, ForecastMetrics]:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.linear_model import Ridge

    X = _feature_frame(series.index)
    y = series.values

    holdout = min(max(3, len(series) // 5), 30)
    X_train, X_test = X.iloc[:-holdout], X.iloc[-holdout:]
    y_train, y_test = y[:-holdout], y[-holdout:]

    estimator = RandomForestRegressor(n_estimators=200, max_depth=8, random_state=42) if model == "rf" else Ridge(alpha=1.0)
    estimator.fit(X_train, y_train)
    test_pred = estimator.predict(X_test)
    mae, mape = _holdout_metrics(y_test, test_pred)

    # Refit on the full history for the actual future forecast.
    full_estimator = RandomForestRegressor(n_estimators=200, max_depth=8, random_state=42) if model == "rf" else Ridge(alpha=1.0)
    full_estimator.fit(X, y)

    future_idx = pd.date_range(series.index[-1], periods=periods + 1, freq=freq)[1:]
    future_index_full = pd.date_range(series.index[0], future_idx[-1], freq=freq)
    X_future = _feature_frame(future_index_full).iloc[-periods:]
    future_vals = np.clip(full_estimator.predict(X_future), 0, None)

    residual_std = float(np.std(y_train - estimator.predict(X_train)) or 0)
    hist = pd.DataFrame({"date": series.index, "actual": series.values, "forecast": np.nan, "lower": np.nan, "upper": np.nan})
    fut = pd.DataFrame({
        "date": future_idx, "actual": np.nan, "forecast": future_vals,
        "lower": np.clip(future_vals - 1.28 * residual_std, 0, None),
        "upper": future_vals + 1.28 * residual_std,
    })
    out = pd.concat([hist, fut], ignore_index=True)
    metrics = ForecastMetrics(
        mae=mae, mape_pct=mape, historical_total=float(series.sum()), forecast_total=float(future_vals.sum()),
        expected_growth_pct=float((future_vals.mean() - series.tail(periods).mean()) / max(series.tail(periods).mean(), 1e-9) * 100),
    )
    return out, metrics
