"""Natural-language querying over a DataFrame ("Chat with your Data").

Uses a small set of deterministic intent patterns (works with zero LLM
configuration) and, when an LLM provider is available, asks it to phrase
the final answer in natural language from the *computed* pandas result —
the model never invents numbers, it only narrates them.
"""
from __future__ import annotations

import re

import pandas as pd

import llm
from core.utils import numeric_columns
from llm.prompts import CHAT_PROMPT, CHAT_SYSTEM

SUGGESTED_QUESTIONS = [
    "What is the total revenue?",
    "Show me the top 5 by revenue",
    "What is the average order value?",
    "How many unique customers are there?",
    "Show revenue trend over time",
    "What is the profit margin?",
]


def _find_column(df: pd.DataFrame, mapping: dict, role_or_name: str) -> str | None:
    if mapping.get(role_or_name):
        return mapping[role_or_name]
    matches = [c for c in df.columns if role_or_name.lower() in str(c).lower()]
    return matches[0] if matches else None


def answer(df: pd.DataFrame, mapping: dict, question: str) -> tuple[str, pd.DataFrame | None]:
    """Answer a natural-language question. Returns (text_answer, optional_table)."""
    q = question.lower().strip()
    revenue_c, profit_c, date_c = mapping.get("revenue"), mapping.get("profit"), mapping.get("date")

    result_text: str
    table: pd.DataFrame | None = None

    if re.search(r"\btotal\b.*\brevenue\b|\brevenue\b.*\btotal\b", q) and revenue_c:
        total = pd.to_numeric(df[revenue_c], errors="coerce").sum()
        result_text = f"Total {revenue_c} is {total:,.2f}."
    elif re.search(r"\baverage\b.*(order|revenue)|\bmean\b.*(order|revenue)", q) and revenue_c:
        avg = pd.to_numeric(df[revenue_c], errors="coerce").mean()
        result_text = f"The average {revenue_c} is {avg:,.2f}."
    elif re.search(r"\bmargin\b|\bprofitab", q) and profit_c and revenue_c:
        rev = pd.to_numeric(df[revenue_c], errors="coerce").sum()
        profit = pd.to_numeric(df[profit_c], errors="coerce").sum()
        margin = profit / rev * 100 if rev else 0
        result_text = f"Overall profit margin is {margin:.2f}% (profit {profit:,.2f} / revenue {rev:,.2f})."
    elif re.search(r"\bhow many\b.*\bcustomer|\bunique\b.*\bcustomer", q) and mapping.get("customer_id"):
        n = df[mapping["customer_id"]].nunique()
        result_text = f"There are {n:,} unique customers."
    elif re.search(r"\btop\s*(\d+)?", q):
        n_match = re.search(r"top\s*(\d+)", q)
        n = int(n_match.group(1)) if n_match else 5
        group_col = mapping.get("product") or mapping.get("category") or mapping.get("region")
        value_col = revenue_c
        if group_col and value_col:
            table = (
                df.assign(__v=pd.to_numeric(df[value_col], errors="coerce"))
                .groupby(group_col, dropna=False)["__v"].sum().sort_values(ascending=False)
                .head(n).reset_index().rename(columns={"__v": value_col})
            )
            result_text = f"Here are the top {n} {group_col} by {value_col}."
        else:
            table = df.head(n)
            result_text = f"Here are the first {n} rows."
    elif re.search(r"\btrend\b|\bover time\b", q) and revenue_c and date_c:
        from analytics.kpis import revenue_by_period

        table = revenue_by_period(df, mapping, freq="M")
        result_text = f"Here's the {revenue_c} trend by month."
    elif re.search(r"\bhow many rows|\bshape\b|\bsize\b", q):
        result_text = f"The dataset has {len(df):,} rows and {df.shape[1]} columns."
    elif re.search(r"\bcolumns?\b", q):
        result_text = "Columns: " + ", ".join(str(c) for c in df.columns)
    elif re.search(r"\bmissing\b|\bnull", q):
        missing = int(df.isna().sum().sum())
        result_text = f"There are {missing:,} missing values across the dataset."
    elif re.search(r"\bduplicate", q):
        dupes = int(df.duplicated().sum())
        result_text = f"There are {dupes:,} duplicate rows."
    else:
        # Fallback: try to find a numeric column named in the question and sum it.
        candidates = numeric_columns(df)
        target = next((c for c in candidates if str(c).lower() in q), None)
        if target:
            total = pd.to_numeric(df[target], errors="coerce").sum()
            result_text = f"Total {target} is {total:,.2f}."
        else:
            result_text = (
                "I couldn't map that question to a computed result yet. Try asking about "
                "revenue, profit, customers, top products, trends, or data quality."
            )

    if llm.is_available():
        try:
            schema = {r: v for r, v in mapping.items() if v}
            narrated = llm.generate(
                CHAT_PROMPT.format(schema=schema, question=question, result=result_text),
                system=CHAT_SYSTEM, max_tokens=300,
            )
            if narrated:
                result_text = narrated
        except llm.LLMUnavailableError:
            pass

    return result_text, table
