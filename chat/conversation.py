"""Conversation-history helpers for the Chat-with-Data page.

Thin wrapper around :mod:`database.repository` that also keeps a fast
in-memory copy for the current Streamlit run.
"""
from __future__ import annotations

from database import repository
from models import ChatMessage


def record(session_id: str, dataset: str, role: str, content: str) -> None:
    repository.add_chat_message(session_id, dataset, role, content)


def history(session_id: str, limit: int = 100) -> list[ChatMessage]:
    df = repository.recent_chat(session_id, limit)
    if df.empty:
        return []
    df = df.sort_values("id")
    return [ChatMessage(role=row.role, content=row.message) for row in df.itertuples()]
