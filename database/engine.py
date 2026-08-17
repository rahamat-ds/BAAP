"""SQLite persistence layer: engine bootstrap and schema management.

InsightFlow runs as a single-user local analytics tool (no auth wall), so
this database exists purely to back *session management* — remembering
datasets loaded, reports generated, chat transcripts, saved SQL queries and
an activity log — across app restarts.
"""
from __future__ import annotations

from sqlalchemy import Engine, create_engine, text

from config import DB_PATH
from core.logging_config import get_logger

logger = get_logger(__name__)

_ENGINE: Engine | None = None

SCHEMA: list[str] = [
    """CREATE TABLE IF NOT EXISTS datasets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        name TEXT,
        source TEXT,
        rows INTEGER,
        cols INTEGER,
        created_at TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        name TEXT,
        kind TEXT,
        path TEXT,
        created_at TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        dataset TEXT,
        role TEXT,
        message TEXT,
        created_at TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS activity_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        action TEXT,
        detail TEXT,
        created_at TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS saved_queries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        name TEXT,
        sql TEXT,
        created_at TEXT
    )""",
]


def engine() -> Engine:
    """Return the process-wide SQLAlchemy engine, creating the schema once."""
    global _ENGINE
    if _ENGINE is None:
        logger.info("Initializing SQLite database at %s", DB_PATH)
        _ENGINE = create_engine(f"sqlite:///{DB_PATH}", future=True)
        with _ENGINE.begin() as conn:
            for statement in SCHEMA:
                conn.execute(text(statement))
    return _ENGINE
