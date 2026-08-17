"""KPI computation, generalized to work off the semantic column mapping."""
from __future__ import annotations

import pandas as pd

from models import KPIResult


def _period_over_period(df: pd.DataFrame, date_col: str, value_col: str) -> float | None:
    """Return the % change between the last and previous calendar month."""
    parsed = pd.to_datetime(df[date_col], errors="coerce")
    monthly = (
        pd.DataFrame({"date": parsed, "value": pd.to_numeric(df[value_col], errors="coerce")})
        .dropna(subset=["date"])
        .assign(period=lambda d: d["date"].dt.to_period("M"))
        .groupby("period")["value"].sum()
        .sort_index()
    )
    if len(monthly) < 2:
        return None
    prev, last = monthly.iloc[-2], monthly.iloc[-1]
    if prev == 0:
        return None
    return float((last - prev) / abs(prev) * 100)


def compute_core_kpis(df: pd.DataFrame, mapping: dict) -> list[KPIResult]:
    """Compute the headline KPI row shown on the dashboard."""
    results: list[KPIResult] = []
    revenue_c, profit_c, cost_c = mapping.get("revenue"), mapping.get("profit"), mapping.get("cost")
    order_c, customer_c, date_c, qty_c = (
        mapping.get("order_id"), mapping.get("customer_id"), mapping.get("date"), mapping.get("quantity"),
    )

    results.append(KPIResult("Total Rows", float(len(df))))

    if revenue_c:
        total_rev = float(pd.to_numeric(df[revenue_c], errors="coerce").sum())
        delta = _period_over_period(df, date_c, revenue_c) if date_c else None
        results.append(KPIResult("Total Revenue", total_rev, delta))

    if profit_c:
        total_profit = float(pd.to_numeric(df[profit_c], errors="coerce").sum())
        delta = _period_over_period(df, date_c, profit_c) if date_c else None
        results.append(KPIResult("Total Profit", total_profit, delta))
        if revenue_c and total_profit is not None:
            total_rev = float(pd.to_numeric(df[revenue_c], errors="coerce").sum())
            margin = (total_profit / total_rev * 100) if total_rev else None
            results.append(KPIResult("Profit Margin %", margin))
    elif revenue_c and cost_c:
        rev = pd.to_numeric(df[revenue_c], errors="coerce")
        cost = pd.to_numeric(df[cost_c], errors="coerce")
        total_profit = float((rev - cost).sum())
        results.append(KPIResult("Total Profit (est.)", total_profit))
        margin = float(total_profit / rev.sum() * 100) if rev.sum() else None
        results.append(KPIResult("Profit Margin % (est.)", margin))

    if order_c:
        results.append(KPIResult("Total Orders", float(df[order_c].nunique())))
        if revenue_c:
            aov = float(pd.to_numeric(df[revenue_c], errors="coerce").sum() / max(df[order_c].nunique(), 1))
            results.append(KPIResult("Avg Order Value", aov))
    elif revenue_c:
        results.append(KPIResult("Avg Order Value", float(pd.to_numeric(df[revenue_c], errors="coerce").mean())))

    if customer_c:
        results.append(KPIResult("Unique Customers", float(df[customer_c].nunique())))
        if revenue_c:
            rev_per_cust = float(pd.to_numeric(df[revenue_c], errors="coerce").sum() / max(df[customer_c].nunique(), 1))
            results.append(KPIResult("Revenue / Customer", rev_per_cust))

    if qty_c:
        results.append(KPIResult("Units Sold", float(pd.to_numeric(df[qty_c], errors="coerce").sum())))

    return results


def revenue_by_period(df: pd.DataFrame, mapping: dict, freq: str = "M") -> pd.DataFrame:
    """Aggregate the revenue metric by calendar period for trend charts."""
    date_c, revenue_c = mapping.get("date"), mapping.get("revenue")
    if not date_c or not revenue_c:
        return pd.DataFrame()
    parsed = pd.to_datetime(df[date_c], errors="coerce")
    values = pd.to_numeric(df[revenue_c], errors="coerce")
    out = (
        pd.DataFrame({"period": parsed, "value": values})
        .dropna(subset=["period"])
        .assign(period=lambda d: d["period"].dt.to_period(freq).dt.to_timestamp())
        .groupby("period", as_index=False)["value"].sum()
        .sort_values("period")
    )
    return out


def top_n(df: pd.DataFrame, group_col: str, value_col: str, n: int = 10, agg: str = "sum") -> pd.DataFrame:
    if not group_col or not value_col:
        return pd.DataFrame()
    values = pd.to_numeric(df[value_col], errors="coerce")
    out = (
        df.assign(__value=values)
        .groupby(group_col, dropna=False)["__value"].agg(agg)
        .sort_values(ascending=False)
        .head(n)
        .reset_index()
        .rename(columns={"__value": value_col})
    )
    return out
