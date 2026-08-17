"""Orchestrates the full "load a dataset" workflow: ingest -> validate ->
register in session -> log to the history database.
"""
from __future__ import annotations

import pandas as pd

from core.logging_config import get_logger
from database import repository
from pipelines import ingestion
from services import session_service

logger = get_logger(__name__)


def load_uploaded_file(filename: str, raw: bytes) -> list[tuple[str, pd.DataFrame, dict]]:
    """Parse an uploaded file and return [(suggested_name, df, meta), ...].

    A single upload can yield multiple frames (multi-sheet Excel, a zip of
    CSVs, or a SQLite file with several tables).
    """
    frames, meta = ingestion.load_any(filename, raw)
    return [(name, df, meta) for name, df in frames.items()]


def register_and_log(name: str, df: pd.DataFrame, source: str, make_active: bool = True) -> str:
    registered_name = session_service.register_dataset(name, df, source=source, make_active=make_active)
    repository.add_dataset(session_service.session_id(), registered_name, source, len(df), df.shape[1])
    repository.log_activity(session_service.session_id(), "dataset_loaded", {"name": registered_name, "source": source})
    return registered_name


def load_sample_dataset() -> str:
    name, df = ingestion.load_sample()
    return register_and_log(name, df, source="sample")
