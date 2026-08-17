"""Typed data structures shared across pipelines, analytics and the UI.

DataFrames remain the primary currency for tabular data throughout the
codebase (that's the right tool for the job); these dataclasses are used
where a *structured, typed result* clarifies an API — quality scores,
validation reports, forecast diagnostics, chat turns, and the like.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass(slots=True)
class QualityOverview:
    """High-level structural profile of a dataset."""

    rows: int
    columns: int
    duplicate_rows: int
    missing_cells: int
    missing_pct: float
    memory_mb: float
    numeric_cols: int
    text_cols: int
    quality_score: int = 0


@dataclass(slots=True)
class ValidationCheck:
    """Result of a single business-rule validation check."""

    name: str
    passed: bool
    count: int
    severity: Severity = Severity.WARNING
    description: str = ""


@dataclass(slots=True)
class ValidationReport:
    """Aggregate result of running all applicable validation checks."""

    checks: list[ValidationCheck] = field(default_factory=list)

    @property
    def score(self) -> int:
        if not self.checks:
            return 100
        passed = sum(1 for c in self.checks if c.passed)
        return round(passed / len(self.checks) * 100)

    @property
    def failed_checks(self) -> list[ValidationCheck]:
        return [c for c in self.checks if not c.passed]


@dataclass(slots=True)
class CleaningStepResult:
    """Outcome of a single data-cleaning operation."""

    message: str
    rows_before: int
    rows_after: int
    applied_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(slots=True)
class KPIResult:
    """A single KPI value with an optional period-over-period delta."""

    name: str
    value: Optional[float]
    delta_pct: Optional[float] = None
    formatted: str = ""


@dataclass(slots=True)
class ForecastMetrics:
    """Diagnostics returned alongside a forecast."""

    mae: Optional[float] = None
    mape_pct: Optional[float] = None
    historical_total: Optional[float] = None
    forecast_total: Optional[float] = None
    expected_growth_pct: Optional[float] = None


@dataclass(slots=True)
class ChatMessage:
    """A single turn in a Chat-with-Data conversation."""

    role: str  # "user" | "assistant"
    content: str
    table: Optional[Any] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(slots=True)
class DatasetMeta:
    """Metadata describing a registered in-session dataset."""

    name: str
    source: str
    rows: int
    cols: int
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(slots=True)
class ReportRequest:
    """Parameters used to build a generated report."""

    dataset_name: str
    title: str = "Business Performance Report"
    include_insights: bool = True
    include_charts: bool = True
    tables: list[str] = field(default_factory=list)
