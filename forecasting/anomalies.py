"""Anomaly detection over numeric columns or a mapped revenue/date series."""
from __future__ import annotations

import numpy as np
import pandas as pd


def detect_zscore(df: pd.DataFrame, column: str, threshold: float = 3.0) -> pd.DataFrame:
    series = pd.to_numeric(df[column], errors="coerce")
    z = (series - series.mean()) / (series.std() or 1)
    out = df.copy()
    out["_zscore"] = z
    out["_is_anomaly"] = z.abs() > threshold
    return out[out["_is_anomaly"]].drop(columns="_is_anomaly")


def detect_iqr(df: pd.DataFrame, column: str, factor: float = 1.5) -> pd.DataFrame:
    series = pd.to_numeric(df[column], errors="coerce")
    q1, q3 = series.quantile(0.25), series.quantile(0.75)
    iqr = q3 - q1
    lo, hi = q1 - factor * iqr, q3 + factor * iqr
    out = df.copy()
    out["_is_anomaly"] = (series < lo) | (series > hi)
    return out[out["_is_anomaly"]].drop(columns="_is_anomaly")


def detect_isolation_forest(df: pd.DataFrame, columns: list[str], contamination: float = 0.03) -> pd.DataFrame:
    from sklearn.ensemble import IsolationForest

    numeric = df[columns].apply(pd.to_numeric, errors="coerce").fillna(0)
    if len(numeric) < 10:
        return df.iloc[0:0]
    model = IsolationForest(contamination=contamination, random_state=42, n_estimators=200)
    labels = model.fit_predict(numeric)
    out = df.copy()
    out["_anomaly_score"] = model.decision_function(numeric)
    out["_is_anomaly"] = labels == -1
    return out[out["_is_anomaly"]].drop(columns="_is_anomaly").sort_values("_anomaly_score")


def detect_time_series_anomalies(df: pd.DataFrame, mapping: dict, threshold: float = 3.0) -> pd.DataFrame:
    """Flag daily revenue totals that deviate sharply from a rolling baseline."""
    date_c, revenue_c = mapping.get("date"), mapping.get("revenue")
    if not date_c or not revenue_c:
        return pd.DataFrame()
    parsed = pd.to_datetime(df[date_c], errors="coerce")
    values = pd.to_numeric(df[revenue_c], errors="coerce")
    daily = pd.DataFrame({"date": parsed, "value": values}).dropna(subset=["date"]).groupby("date")["value"].sum().sort_index()
    if len(daily) < 8:
        return pd.DataFrame()

    rolling_mean = daily.rolling(7, min_periods=3).mean()
    rolling_std = daily.rolling(7, min_periods=3).std().replace(0, np.nan)
    z = (daily - rolling_mean) / rolling_std
    anomalies = daily[z.abs() > threshold]
    return pd.DataFrame({"date": anomalies.index, "value": anomalies.values, "z_score": z.loc[anomalies.index].values})


def anomaly_summary(anomalies: pd.DataFrame, total_rows: int) -> dict:
    return {
        "count": len(anomalies),
        "pct_of_data": round(len(anomalies) / max(total_rows, 1) * 100, 2),
    }
