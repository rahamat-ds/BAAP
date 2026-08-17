"""Retail Operations analytics — courier performance, RTO/returns, shipping.

This module is BAAP's original differentiator: deep logistics
analytics for e-commerce order data (courier, RTO, shipping mode, delivery
days). It is entirely optional — it auto-detects its own extended roles on
top of the core mapping and simply reports "not applicable" content when a
dataset doesn't carry retail-operations columns, so generic datasets are
unaffected.
"""
from __future__ import annotations

import pandas as pd

from core.mapping import auto_map_retail


def detect(df: pd.DataFrame, core_mapping: dict) -> dict[str, str | None]:
    """Auto-map the optional retail-operations roles for this dataset."""
    used = {v for v in core_mapping.values() if v}
    return auto_map_retail(df, exclude=used)


def is_applicable(retail_mapping: dict) -> bool:
    return any(retail_mapping.values())


def courier_performance(df: pd.DataFrame, core_mapping: dict, retail_mapping: dict) -> pd.DataFrame:
    courier_c = retail_mapping.get("courier")
    if not courier_c:
        return pd.DataFrame()

    agg_spec: dict[str, tuple] = {"orders": (courier_c, "count")}
    if retail_mapping.get("delivery_days"):
        agg_spec["avg_delivery_days"] = (retail_mapping["delivery_days"], "mean")
    if retail_mapping.get("rto"):
        agg_spec["rto_count"] = (retail_mapping["rto"], lambda s: s.astype(str).str.lower().isin(
            ["1", "true", "yes", "y"]).sum())
    if core_mapping.get("revenue"):
        agg_spec["revenue"] = (core_mapping["revenue"], "sum")

    out = df.groupby(courier_c, dropna=False).agg(**agg_spec).reset_index()
    if "rto_count" in out.columns:
        out["rto_rate_pct"] = (out["rto_count"] / out["orders"] * 100).round(2)
    return out.sort_values("orders", ascending=False).reset_index(drop=True)


def rto_analysis(df: pd.DataFrame, retail_mapping: dict) -> pd.DataFrame:
    rto_c = retail_mapping.get("rto")
    if not rto_c:
        return pd.DataFrame()
    flags = df[rto_c].astype(str).str.lower().isin(["1", "true", "yes", "y"])
    rate = float(flags.mean() * 100)
    return pd.DataFrame([{"total_orders": len(df), "rto_orders": int(flags.sum()), "rto_rate_pct": round(rate, 2)}])


def shipping_mode_breakdown(df: pd.DataFrame, retail_mapping: dict) -> pd.DataFrame:
    mode_c, days_c = retail_mapping.get("shipping_mode"), retail_mapping.get("delivery_days")
    if not mode_c:
        return pd.DataFrame()
    agg_spec: dict[str, tuple] = {"orders": (mode_c, "count")}
    if days_c:
        agg_spec["avg_delivery_days"] = (days_c, "mean")
    return df.groupby(mode_c, dropna=False).agg(**agg_spec).reset_index().sort_values("orders", ascending=False)


def delivery_time_distribution(df: pd.DataFrame, retail_mapping: dict) -> pd.DataFrame:
    days_c = retail_mapping.get("delivery_days")
    if not days_c:
        return pd.DataFrame()
    return df[[days_c]].dropna().rename(columns={days_c: "delivery_days"})
