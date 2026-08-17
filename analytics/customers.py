"""Customer analytics: RFM segmentation, lifetime value, churn risk."""
from __future__ import annotations

import pandas as pd


def rfm_analysis(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    """Recency / Frequency / Monetary segmentation per customer."""
    customer_c, date_c, revenue_c, order_c = (
        mapping.get("customer_id"), mapping.get("date"), mapping.get("revenue"), mapping.get("order_id"),
    )
    if not customer_c or not date_c or not revenue_c:
        return pd.DataFrame()

    work = pd.DataFrame({
        "customer": df[customer_c],
        "date": pd.to_datetime(df[date_c], errors="coerce"),
        "revenue": pd.to_numeric(df[revenue_c], errors="coerce"),
        "order": df[order_c] if order_c else df.index,
    }).dropna(subset=["date", "customer"])

    if work.empty:
        return pd.DataFrame()

    snapshot = work["date"].max() + pd.Timedelta(days=1)
    rfm = work.groupby("customer").agg(
        recency=("date", lambda s: (snapshot - s.max()).days),
        frequency=("order", "nunique"),
        monetary=("revenue", "sum"),
    ).reset_index()

    rfm["R"] = pd.qcut(rfm["recency"], 4, labels=[4, 3, 2, 1], duplicates="drop").astype(int)
    rfm["F"] = pd.qcut(rfm["frequency"].rank(method="first"), 4, labels=[1, 2, 3, 4], duplicates="drop").astype(int)
    rfm["M"] = pd.qcut(rfm["monetary"].rank(method="first"), 4, labels=[1, 2, 3, 4], duplicates="drop").astype(int)
    rfm["rfm_score"] = rfm["R"] + rfm["F"] + rfm["M"]

    def segment(row) -> str:
        if row["rfm_score"] >= 10:
            return "Champions"
        if row["R"] >= 3 and row["F"] >= 3:
            return "Loyal Customers"
        if row["R"] >= 3 and row["F"] < 3:
            return "Potential Loyalists"
        if row["R"] <= 2 and row["F"] >= 3:
            return "At Risk"
        if row["R"] <= 2 and row["F"] <= 2 and row["M"] >= 3:
            return "Cannot Lose Them"
        return "Hibernating"

    rfm["segment"] = rfm.apply(segment, axis=1)
    return rfm.sort_values("monetary", ascending=False).reset_index(drop=True)


def customer_lifetime_value(rfm: pd.DataFrame, avg_lifespan_years: float = 2.0) -> pd.DataFrame:
    """Simple CLV estimate: avg order value x purchase frequency x lifespan."""
    if rfm.empty:
        return rfm
    out = rfm.copy()
    out["avg_order_value"] = out["monetary"] / out["frequency"].replace(0, 1)
    annual_frequency = out["frequency"] / max(1, avg_lifespan_years)
    out["estimated_clv"] = out["avg_order_value"] * annual_frequency * avg_lifespan_years
    return out.sort_values("estimated_clv", ascending=False)


def churn_risk(rfm: pd.DataFrame, recency_threshold_days: int = 90) -> pd.DataFrame:
    """Flag customers who haven't purchased recently as churn-risk."""
    if rfm.empty:
        return rfm
    out = rfm.copy()
    out["churn_risk"] = out["recency"] > recency_threshold_days
    return out


def segment_summary(rfm: pd.DataFrame) -> pd.DataFrame:
    if rfm.empty:
        return rfm
    return (
        rfm.groupby("segment")
        .agg(customers=("customer", "count"), total_value=("monetary", "sum"), avg_recency=("recency", "mean"))
        .sort_values("total_value", ascending=False)
        .reset_index()
    )
