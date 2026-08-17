"""Product analytics: ABC inventory classification and performance ranking."""
from __future__ import annotations

import pandas as pd


def abc_classification(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    """Classify products into A (top 80% revenue), B (next 15%), C (last 5%)."""
    product_c, revenue_c = mapping.get("product"), mapping.get("revenue")
    if not product_c or not revenue_c:
        return pd.DataFrame()

    grouped = (
        df.assign(__revenue=pd.to_numeric(df[revenue_c], errors="coerce"))
        .groupby(product_c, dropna=False)["__revenue"].sum()
        .sort_values(ascending=False)
        .reset_index()
        .rename(columns={"__revenue": "revenue"})
    )
    total = grouped["revenue"].sum() or 1
    grouped["cum_pct"] = grouped["revenue"].cumsum() / total * 100
    grouped["class"] = grouped["cum_pct"].apply(lambda p: "A" if p <= 80 else ("B" if p <= 95 else "C"))
    grouped["revenue_share_pct"] = (grouped["revenue"] / total * 100).round(2)
    return grouped


def product_performance(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    """Per-product revenue, profit, quantity and order-count summary."""
    product_c = mapping.get("product")
    if not product_c:
        return pd.DataFrame()

    agg_spec: dict[str, tuple] = {}
    if mapping.get("revenue"):
        agg_spec["revenue"] = (mapping["revenue"], "sum")
    if mapping.get("profit"):
        agg_spec["profit"] = (mapping["profit"], "sum")
    if mapping.get("quantity"):
        agg_spec["units_sold"] = (mapping["quantity"], "sum")
    if mapping.get("order_id"):
        agg_spec["orders"] = (mapping["order_id"], "nunique")
    if not agg_spec:
        agg_spec["rows"] = (product_c, "count")

    out = df.groupby(product_c, dropna=False).agg(**agg_spec).reset_index()
    sort_col = "revenue" if "revenue" in out.columns else out.columns[-1]
    return out.sort_values(sort_col, ascending=False).reset_index(drop=True)


def category_performance(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    category_c, revenue_c = mapping.get("category"), mapping.get("revenue")
    if not category_c or not revenue_c:
        return pd.DataFrame()
    out = (
        df.assign(__revenue=pd.to_numeric(df[revenue_c], errors="coerce"))
        .groupby(category_c, dropna=False)
        .agg(revenue=("__revenue", "sum"), orders=("__revenue", "count"))
        .reset_index()
        .sort_values("revenue", ascending=False)
    )
    return out
