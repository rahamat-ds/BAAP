"""Repository functions: the only place in the codebase that writes SQL.

Every function is a thin, typed wrapper around the ``activity_log`` /
``datasets`` / ``reports`` / ``chat_messages`` / ``saved_queries`` tables so
callers never construct SQL themselves.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import pandas as pd
from sqlalchemy import text

from .engine import engine


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def execute(sql: str, params: dict | None = None) -> None:
    with engine().begin() as conn:
        conn.execute(text(sql), params or {})


def query_df(sql: str, params: dict | None = None) -> pd.DataFrame:
    with engine().begin() as conn:
        rows = conn.execute(text(sql), params or {}).mappings().all()
        return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# Activity log ("session management")
# --------------------------------------------------------------------------
def log_activity(session_id: str, action: str, detail: Any = "") -> None:
    if isinstance(detail, (dict, list)):
        detail = json.dumps(detail, default=str)
    execute(
        "INSERT INTO activity_log (session_id, action, detail, created_at) "
        "VALUES (:s, :a, :d, :t)",
        {"s": session_id, "a": action, "d": str(detail)[:800], "t": _now()},
    )


def recent_activity(session_id: str | None = None, limit: int = 50) -> pd.DataFrame:
    return _recent("activity_log", session_id, limit)


# --------------------------------------------------------------------------
# Datasets
# --------------------------------------------------------------------------
def add_dataset(session_id: str, name: str, source: str, rows: int, cols: int) -> None:
    execute(
        "INSERT INTO datasets (session_id, name, source, rows, cols, created_at) "
        "VALUES (:s, :n, :src, :r, :c, :t)",
        {"s": session_id, "n": name, "src": source, "r": int(rows), "c": int(cols), "t": _now()},
    )


def recent_datasets(session_id: str | None = None, limit: int = 50) -> pd.DataFrame:
    return _recent("datasets", session_id, limit)


# --------------------------------------------------------------------------
# Reports
# --------------------------------------------------------------------------
def add_report(session_id: str, name: str, kind: str, path: str) -> None:
    execute(
        "INSERT INTO reports (session_id, name, kind, path, created_at) "
        "VALUES (:s, :n, :k, :p, :t)",
        {"s": session_id, "n": name, "k": kind, "p": str(path), "t": _now()},
    )


def recent_reports(session_id: str | None = None, limit: int = 50) -> pd.DataFrame:
    return _recent("reports", session_id, limit)


# --------------------------------------------------------------------------
# Chat
# --------------------------------------------------------------------------
def add_chat_message(session_id: str, dataset: str, role: str, message: str) -> None:
    execute(
        "INSERT INTO chat_messages (session_id, dataset, role, message, created_at) "
        "VALUES (:s, :d, :r, :m, :t)",
        {"s": session_id, "d": dataset, "r": role, "m": message, "t": _now()},
    )


def recent_chat(session_id: str | None = None, limit: int = 100) -> pd.DataFrame:
    return _recent("chat_messages", session_id, limit)


# --------------------------------------------------------------------------
# Saved SQL queries
# --------------------------------------------------------------------------
def save_query(session_id: str, name: str, sql: str) -> None:
    execute(
        "INSERT INTO saved_queries (session_id, name, sql, created_at) VALUES (:s, :n, :q, :t)",
        {"s": session_id, "n": name, "q": sql, "t": _now()},
    )


def recent_queries(session_id: str | None = None, limit: int = 20) -> pd.DataFrame:
    return _recent("saved_queries", session_id, limit)


# --------------------------------------------------------------------------
# Housekeeping
# --------------------------------------------------------------------------
def clear_session(session_id: str) -> None:
    for table in ("datasets", "reports", "chat_messages", "activity_log", "saved_queries"):
        execute(f"DELETE FROM {table} WHERE session_id=:s", {"s": session_id})


def _recent(table: str, session_id: str | None, limit: int) -> pd.DataFrame:
    if session_id:
        return query_df(
            f"SELECT * FROM {table} WHERE session_id=:s ORDER BY id DESC LIMIT {int(limit)}",
            {"s": session_id},
        )
    return query_df(f"SELECT * FROM {table} ORDER BY id DESC LIMIT {int(limit)}")
