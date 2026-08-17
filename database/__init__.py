"""SQLite-backed persistence for session history: datasets, reports, chat
transcripts, saved SQL queries and an activity log.
"""
from .engine import engine
from . import repository

__all__ = ["engine", "repository"]
