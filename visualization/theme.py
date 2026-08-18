"""Application theme: CSS injection and reusable page-chrome components.

A single dark, professional SaaS theme with an indigo/teal accent —
BAAP's visual identity. All pages call these helpers instead of
writing raw HTML/CSS inline, so the look stays consistent and easy to
retheme from one place.
"""
from __future__ import annotations

import streamlit as st

from config import settings

ACCENT = "#6C5CE7"
ACCENT_SOFT = "#8B7CF6"
POSITIVE = "#26C485"
NEGATIVE = "#EF476F"
WARNING = "#F6A609"
BG = "#0F1117"
SURFACE = "#171A23"
SURFACE_ALT = "#1E2230"
BORDER = "#2A2E3D"
TEXT = "#E6E8F0"
TEXT_MUTED = "#9095A8"

PLOTLY_TEMPLATE = {
    "layout": {
        "paper_bgcolor": SURFACE,
        "plot_bgcolor": SURFACE,
        "font": {"color": TEXT, "family": "Inter, sans-serif"},
        "colorway": ["#6C5CE7", "#00B8A9", "#F6A609", "#EF476F", "#5B7CFA",
                     "#26C485", "#EC4899", "#38BDF8", "#F97316", "#14B8A6"],
        "xaxis": {"gridcolor": BORDER, "zerolinecolor": BORDER},
        "yaxis": {"gridcolor": BORDER, "zerolinecolor": BORDER},
        "legend": {"bgcolor": "rgba(0,0,0,0)"},
        "margin": {"t": 48, "l": 10, "r": 10, "b": 10},
    }
}


def inject_css() -> None:
    st.markdown(
        f"""
        <style>
        .stApp {{ background-color: {BG}; }}
        section[data-testid="stSidebar"] {{ background-color: {SURFACE}; border-right: 1px solid {BORDER}; }}
        h1, h2, h3, h4 {{ color: {TEXT}; font-weight: 700; }}
        p, span, label, li {{ color: {TEXT}; }}
        .if-card {{
            background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 14px;
            padding: 1.1rem 1.3rem; margin-bottom: 0.9rem;
        }}
        .if-kpi {{
            background: linear-gradient(145deg, {SURFACE_ALT}, {SURFACE});
            border: 1px solid {BORDER}; border-radius: 14px; padding: 1rem 1.2rem;
        }}
        .if-kpi .label {{ color: {TEXT_MUTED}; font-size: 0.80rem; text-transform: uppercase; letter-spacing: .04em; }}
        .if-kpi .value {{ color: {TEXT}; font-size: 1.7rem; font-weight: 700; margin-top: 2px; }}
        .if-kpi .delta-pos {{ color: {POSITIVE}; font-size: 0.85rem; font-weight: 600; }}
        .if-kpi .delta-neg {{ color: {NEGATIVE}; font-size: 0.85rem; font-weight: 600; }}
        .if-badge {{
            display: inline-block; padding: 2px 10px; border-radius: 999px;
            font-size: 0.75rem; font-weight: 600; background: {ACCENT}22; color: {ACCENT_SOFT};
        }}
        .if-header {{
            display: flex; align-items: center; gap: .6rem; margin-bottom: .2rem;
        }}
        .if-header .icon {{ font-size: 1.9rem; }}
        .if-subtitle {{ color: {TEXT_MUTED}; font-size: 0.95rem; margin-bottom: 1.1rem; }}
        .if-insight {{
            border-left: 3px solid {ACCENT}; background: {SURFACE_ALT};
            border-radius: 0 10px 10px 0; padding: 0.75rem 1rem; margin-bottom: 0.6rem;
        }}
        div[data-testid="stMetricValue"] {{ color: {TEXT}; }}
        .stButton>button {{ border-radius: 10px; border: 1px solid {BORDER}; }}
        .stButton>button[kind="primary"] {{ background: {ACCENT}; border-color: {ACCENT}; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str = "", icon: str = "") -> None:
    st.markdown(
        f'<div class="if-header"><h1 style="margin:0">{title}</h1></div>',
        unsafe_allow_html=True,
    )
    if subtitle:
        st.markdown(f'<div class="if-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def kpi_card(label: str, value: str, delta_pct: float | None = None) -> str:
    delta_html = ""
    if delta_pct is not None:
        cls = "delta-pos" if delta_pct >= 0 else "delta-neg"
        arrow = "\u25b2" if delta_pct >= 0 else "\u25bc"
        delta_html = f'<div class="{cls}">{arrow} {abs(delta_pct):.1f}%</div>'
    return f'<div class="if-kpi"><div class="label">{label}</div><div class="value">{value}</div>{delta_html}</div>'

def render_kpi_row(kpis, currency_fields: set[str] | None = None) -> None:
    """Render a list of models.KPIResult as a responsive KPI card row."""
    currency_fields = currency_fields or set()
    cols = st.columns(min(len(kpis), 5) or 1)
    for i, kpi in enumerate(kpis):
        with cols[i % len(cols)]:
            if kpi.value is None:
                formatted = "—"
            elif kpi.name in currency_fields:
                formatted = f"{settings.currency_symbol}{kpi.value:,.0f}"
            elif "%" in kpi.name:
                formatted = f"{kpi.value:,.1f}%"
            elif kpi.value == int(kpi.value):
                formatted = f"{kpi.value:,.0f}"
            else:
                formatted = f"{kpi.value:,.2f}"
            st.markdown(kpi_card(kpi.name, formatted, kpi.delta_pct), unsafe_allow_html=True)


def insight_card(text: str) -> None:
    st.markdown(f'<div class="if-insight">{text}</div>', unsafe_allow_html=True)


def badge(text: str) -> str:
    return f'<span class="if-badge">{text}</span>'
