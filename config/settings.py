"""Central application configuration.

All environment-driven configuration lives here so the rest of the codebase
never touches ``os.environ`` directly. Values can be overridden via a local
``.env`` file (loaded automatically if ``python-dotenv`` is installed) or via
real environment variables, which always win.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

try:  # pragma: no cover - optional convenience dependency
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover
    pass


def _env_bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("BAAP_DATA_DIR", ROOT_DIR / "data"))
UPLOAD_DIR = DATA_DIR / "uploads"
REPORT_DIR = DATA_DIR / "reports"
SAMPLE_DIR = DATA_DIR / "samples"
DB_PATH = DATA_DIR / "baap.db"

for _d in (DATA_DIR, UPLOAD_DIR, REPORT_DIR, SAMPLE_DIR):
    _d.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class AppMeta:
    """Product identity — BAAP (Business Analytics Automation Platform)."""

    name: str = "BAAP"
    tagline: str = "Business Analytics Automation Platform"
    icon: str = ""
    version: str = "2.0.0"


@dataclass(frozen=True)
class Settings:
    """Runtime configuration, resolved once at import time."""

    app: AppMeta = field(default_factory=AppMeta)

    currency_symbol: str = field(default_factory=lambda: os.getenv("APP_CURRENCY", "\u20b9"))
    revenue_target: float = field(default_factory=lambda: _env_float("APP_TARGET_REVENUE", 5_000_000))

    # Upload limits
    max_upload_mb: int = field(default_factory=lambda: int(os.getenv("MAX_UPLOAD_MB", "500")))

    # LLM provider keys (all optional — the platform works fully offline)
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    gemini_api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    default_llm_provider: str = field(default_factory=lambda: os.getenv("LLM_PROVIDER", "auto"))

    # Feature flags
    enable_sql_workspace: bool = field(default_factory=lambda: _env_bool("ENABLE_SQL_WORKSPACE", True))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))


settings = Settings()

# --------------------------------------------------------------------------
# Semantic column roles — the backbone of the dataset-agnostic analytics
# engine. Every analytics/forecasting/chat module reads *roles* rather than
# hard-coded column names, so the platform works on any tabular dataset, not
# just the bundled Indian-retail sample.
# --------------------------------------------------------------------------
ROLES: list[str] = [
    "date", "revenue", "profit", "cost", "quantity",
    "order_id", "customer_id", "product", "category", "region",
]

ROLE_LABELS: dict[str, str] = {
    "date": "Order / Transaction Date",
    "revenue": "Revenue / Sales Amount",
    "profit": "Profit",
    "cost": "Cost",
    "quantity": "Quantity",
    "order_id": "Order ID",
    "customer_id": "Customer ID",
    "product": "Product",
    "category": "Category",
    "region": "Region / State / Country",
}

ROLE_PATTERNS: dict[str, str] = {
    "date": r"(order[_ ]?date|invoice[_ ]?date|date|datetime|timestamp|\bday\b|period)",
    "revenue": r"(revenue|sales|amount|total|turnover|gross|net[_ ]?sales)",
    "profit": r"(profit|margin|earnings|net[_ ]?income)",
    "cost": r"(cost|cogs|expense|spend|unit[_ ]?cost)",
    "quantity": r"(qty|quantity|units|volume)",
    "order_id": r"(order[_ ]?id|invoice|transaction|order[_ ]?no|receipt)",
    "customer_id": r"(customer|client|buyer|account|user[_ ]?id)",
    "product": r"(product|item|sku|model)",
    "category": r"(category|segment|dept|department|class)",
    "region": r"(region|country|state|city|market|territory|location)",
}

# Extended, *optional* roles used only by the Retail Operations module. These
# are auto-detected the same way but never required — datasets that lack
# them simply don't see that module's content.
RETAIL_ROLES: list[str] = ["courier", "shipping_mode", "delivery_days", "rto", "discount"]

RETAIL_ROLE_LABELS: dict[str, str] = {
    "courier": "Courier / Delivery Partner",
    "shipping_mode": "Shipping Mode",
    "delivery_days": "Delivery Days",
    "rto": "RTO / Return Flag",
    "discount": "Discount %",
}

RETAIL_ROLE_PATTERNS: dict[str, str] = {
    "courier": r"(courier|carrier|delivery[_ ]?partner|shipper)",
    "shipping_mode": r"(shipping[_ ]?mode|shipment[_ ]?type|delivery[_ ]?mode)",
    "delivery_days": r"(delivery[_ ]?days|transit[_ ]?time|days[_ ]?to[_ ]?deliver)",
    "rto": r"(^rto$|return[_ ]?to[_ ]?origin|is[_ ]?returned|returned)",
    "discount": r"(discount)",
}

# --------------------------------------------------------------------------
# Visualization
# --------------------------------------------------------------------------
CHART_TYPES: list[str] = [
    "Bar", "Line", "Area", "Pie", "Donut", "Scatter", "Bubble", "Histogram",
    "Box Plot", "Heatmap", "Treemap", "Sunburst", "Waterfall", "Correlation Matrix",
]

AGGREGATIONS: list[str] = ["sum", "mean", "median", "count", "min", "max", "nunique"]

PALETTE: list[str] = [
    "#6C5CE7", "#00B8A9", "#F6A609", "#EF476F", "#5B7CFA",
    "#26C485", "#EC4899", "#38BDF8", "#F97316", "#14B8A6",
]

# --------------------------------------------------------------------------
# LLM
# --------------------------------------------------------------------------
LLM_MODELS: dict[str, list[str]] = {
    "anthropic": ["claude-sonnet-4-6", "claude-haiku-4-5"],
    "openai": ["gpt-4o-mini", "gpt-4o"],
    "gemini": ["gemini-2.0-flash", "gemini-1.5-flash"],
}
