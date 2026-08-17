"""Business insight generation: AI-powered when a provider is configured,
always backed by a deterministic rule-based engine so the feature works
fully offline.
"""
from __future__ import annotations

import pandas as pd

import llm
from analytics.kpis import compute_core_kpis, revenue_by_period, top_n
from llm.prompts import INSIGHTS_PROMPT, INSIGHTS_SYSTEM


def rule_based_insights(df: pd.DataFrame, mapping: dict) -> list[str]:
    """Deterministic, always-available insight generation."""
    insights: list[str] = []
    revenue_c, profit_c, date_c = mapping.get("revenue"), mapping.get("profit"), mapping.get("date")
    category_c, region_c, product_c = mapping.get("category"), mapping.get("region"), mapping.get("product")

    if revenue_c and date_c:
        trend = revenue_by_period(df, mapping, freq="M")
        if len(trend) >= 2:
            change = (trend["value"].iloc[-1] - trend["value"].iloc[-2]) / abs(trend["value"].iloc[-2] or 1) * 100
            direction = "grew" if change >= 0 else "declined"
            insights.append(
                f"**Revenue momentum:** Revenue {direction} {abs(change):.1f}% month-over-month "
                f"in the most recent period, moving from {trend['value'].iloc[-2]:,.0f} to {trend['value'].iloc[-1]:,.0f}."
            )
        if len(trend) >= 3:
            best = trend.loc[trend["value"].idxmax()]
            insights.append(
                f"**Peak period:** The strongest period was {best['period'].strftime('%b %Y')} "
                f"with {best['value']:,.0f} in revenue — consider replicating what drove it."
            )

    if revenue_c and category_c:
        cats = top_n(df, category_c, revenue_c, n=3)
        if not cats.empty:
            leader = cats.iloc[0]
            share = leader[revenue_c] / df[revenue_c].astype(float).sum() * 100 if df[revenue_c].sum() else 0
            insights.append(
                f"**Category concentration:** '{leader[category_c]}' leads with "
                f"{leader[revenue_c]:,.0f} in revenue ({share:.1f}% of total)."
            )

    if revenue_c and region_c:
        regions = top_n(df, region_c, revenue_c, n=1)
        if not regions.empty:
            insights.append(f"**Top region:** '{regions.iloc[0][region_c]}' is the highest-revenue region.")

    if revenue_c and product_c:
        products = top_n(df, product_c, revenue_c, n=1)
        if not products.empty:
            insights.append(f"**Top product:** '{products.iloc[0][product_c]}' generates the most revenue.")

    if profit_c and revenue_c:
        margin = float(pd.to_numeric(df[profit_c], errors="coerce").sum()
                        / max(pd.to_numeric(df[revenue_c], errors="coerce").sum(), 1) * 100)
        tone = "healthy" if margin >= 20 else ("thin" if margin >= 5 else "concerning")
        insights.append(f"**Profitability:** Overall profit margin is {margin:.1f}%, which is {tone} for most retail categories.")

    dupes = int(df.duplicated().sum())
    if dupes:
        insights.append(f"**Data quality:** {dupes:,} duplicate rows were detected — clean these before trusting downstream totals.")

    if not insights:
        insights.append("Map more columns (revenue, date, category) in Upload Center to unlock richer insights.")
    return insights


def generate_insights(df: pd.DataFrame, mapping: dict) -> tuple[list[str], str]:
    """Return (insight_list, source) where source is 'ai' or 'rules'."""
    rule_insights = rule_based_insights(df, mapping)
    if not llm.is_available():
        return rule_insights, "rules"

    try:
        kpis = compute_core_kpis(df, mapping)
        metrics_txt = "\n".join(f"- {k.name}: {k.value:,.2f}" for k in kpis if k.value is not None)
        summary_txt = f"{len(df):,} rows, {df.shape[1]} columns. Mapped roles: {mapping}"
        patterns_txt = "\n".join(f"- {i}" for i in rule_insights)
        prompt = INSIGHTS_PROMPT.format(summary=summary_txt, metrics=metrics_txt, patterns=patterns_txt)
        text = llm.generate(prompt, system=INSIGHTS_SYSTEM, max_tokens=900)
        ai_insights = [block.strip() for block in text.split("###") if block.strip()]
        return (ai_insights or rule_insights), ("ai" if ai_insights else "rules")
    except llm.LLMUnavailableError:
        return rule_insights, "rules"


def quick_cards(df: pd.DataFrame, mapping: dict) -> list[dict]:
    """Small headline cards used at the top of the AI Insights page."""
    cards = []
    revenue_c, profit_c = mapping.get("revenue"), mapping.get("profit")
    if revenue_c:
        cards.append({"label": "Total Revenue", "value": float(pd.to_numeric(df[revenue_c], errors="coerce").sum())})
    if profit_c:
        cards.append({"label": "Total Profit", "value": float(pd.to_numeric(df[profit_c], errors="coerce").sum())})
    cards.append({"label": "Data Quality", "value": None, "note": "See Data Profiling for full score"})
    return cards
