"""Business-rule validation.

Generalizes the original InsightFlow validation checks (which were
hard-coded to one exact retail schema and required a column, ``order_id``,
that the project's own generator never produced) so they run against
*any* dataset via the semantic column mapping. A check is skipped rather
than raising when the columns it needs aren't mapped, so partially-mapped
datasets still get a useful, honest score.
"""
from __future__ import annotations

import pandas as pd

from models import Severity, ValidationCheck, ValidationReport


def validate_dataset(df: pd.DataFrame, mapping: dict) -> ValidationReport:
    """Run every applicable business-rule check and return a report."""
    checks: list[ValidationCheck] = []
    revenue_c = mapping.get("revenue")
    profit_c = mapping.get("profit")
    cost_c = mapping.get("cost")
    quantity_c = mapping.get("quantity")
    date_c = mapping.get("date")

    duplicates = int(df.duplicated().sum())
    checks.append(ValidationCheck(
        "Duplicate Rows", duplicates == 0, duplicates, Severity.WARNING,
        "Exact duplicate rows in the dataset.",
    ))

    missing = int(df.isna().sum().sum())
    checks.append(ValidationCheck(
        "Missing Values", missing == 0, missing, Severity.WARNING,
        "Empty cells across all columns.",
    ))

    if revenue_c:
        neg_rev = int((pd.to_numeric(df[revenue_c], errors="coerce") < 0).sum())
        checks.append(ValidationCheck(
            "Negative Revenue", neg_rev == 0, neg_rev, Severity.CRITICAL,
            f"Rows where '{revenue_c}' is negative.",
        ))

    if profit_c:
        neg_profit = int((pd.to_numeric(df[profit_c], errors="coerce") < 0).sum())
        checks.append(ValidationCheck(
            "Negative Profit", neg_profit == 0, neg_profit, Severity.WARNING,
            f"Rows where '{profit_c}' is negative.",
        ))

    if quantity_c:
        bad_qty = int((pd.to_numeric(df[quantity_c], errors="coerce") <= 0).sum())
        checks.append(ValidationCheck(
            "Invalid Quantity", bad_qty == 0, bad_qty, Severity.CRITICAL,
            f"Rows where '{quantity_c}' is zero or negative.",
        ))

    if cost_c:
        bad_cost = int((pd.to_numeric(df[cost_c], errors="coerce") <= 0).sum())
        checks.append(ValidationCheck(
            "Non-Positive Cost", bad_cost == 0, bad_cost, Severity.CRITICAL,
            f"Rows where '{cost_c}' is zero or negative.",
        ))

    if revenue_c and cost_c:
        below_cost = int(
            (pd.to_numeric(df[revenue_c], errors="coerce") < pd.to_numeric(df[cost_c], errors="coerce")).sum()
        )
        checks.append(ValidationCheck(
            "Selling Below Cost", below_cost == 0, below_cost, Severity.CRITICAL,
            f"Rows where '{revenue_c}' is less than '{cost_c}'.",
        ))

    if date_c:
        parsed = pd.to_datetime(df[date_c], errors="coerce")
        future = int((parsed > pd.Timestamp.today()).sum())
        checks.append(ValidationCheck(
            "Future-Dated Rows", future == 0, future, Severity.WARNING,
            f"Rows where '{date_c}' is after today.",
        ))

    return ValidationReport(checks=checks)


def invalid_rows(df: pd.DataFrame, mapping: dict) -> dict[str, pd.DataFrame]:
    """Return the offending rows for each failed check, for drill-down/export."""
    out: dict[str, pd.DataFrame] = {}
    revenue_c, profit_c = mapping.get("revenue"), mapping.get("profit")
    cost_c, quantity_c = mapping.get("cost"), mapping.get("quantity")

    if revenue_c and cost_c:
        out["Selling Below Cost"] = df[
            pd.to_numeric(df[revenue_c], errors="coerce") < pd.to_numeric(df[cost_c], errors="coerce")
        ]
    if revenue_c:
        out["Negative Revenue"] = df[pd.to_numeric(df[revenue_c], errors="coerce") < 0]
    if profit_c:
        out["Negative Profit"] = df[pd.to_numeric(df[profit_c], errors="coerce") < 0]
    if quantity_c:
        out["Invalid Quantity"] = df[pd.to_numeric(df[quantity_c], errors="coerce") <= 0]
    out["Duplicate Rows"] = df[df.duplicated(keep=False)]
    return {k: v for k, v in out.items() if not v.empty}
