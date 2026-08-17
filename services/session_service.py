"""Session/state management: the in-memory registry of loaded datasets.

Wraps ``st.session_state`` so no other module touches it directly. Supports
multiple datasets loaded at once, an active-dataset pointer, per-dataset
column mapping cache, a cleaning-step undo stack, and a stable per-browser-
session id used to scope database history.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Optional

import pandas as pd
import streamlit as st

from core.logging_config import get_logger
from core.mapping import auto_map

logger = get_logger(__name__)

_STATE_KEY = "_insightflow_state"


@dataclass
class _DatasetEntry:
    df: pd.DataFrame
    source: str
    mapping: dict = field(default_factory=dict)
    history: list[pd.DataFrame] = field(default_factory=list)  # undo stack (pre-op snapshots)
    log: list[str] = field(default_factory=list)


@dataclass
class _AppState:
    session_id: str
    datasets: dict[str, _DatasetEntry] = field(default_factory=dict)
    active: Optional[str] = None


def _state() -> _AppState:
    if _STATE_KEY not in st.session_state:
        st.session_state[_STATE_KEY] = _AppState(session_id=str(uuid.uuid4()))
    return st.session_state[_STATE_KEY]


def session_id() -> str:
    return _state().session_id


# --------------------------------------------------------------------------
# Dataset registry
# --------------------------------------------------------------------------
def register_dataset(name: str, df: pd.DataFrame, source: str = "upload", make_active: bool = True) -> str:
    """Register a dataset under a unique display name and return that name."""
    state = _state()
    unique_name = name
    suffix = 2
    while unique_name in state.datasets:
        unique_name = f"{name} ({suffix})"
        suffix += 1

    entry = _DatasetEntry(df=df, source=source, mapping=auto_map(df))
    state.datasets[unique_name] = entry
    if make_active or state.active is None:
        state.active = unique_name
    logger.info("Registered dataset '%s' (%d rows x %d cols)", unique_name, *df.shape)
    return unique_name


def dataset_names() -> list[str]:
    return list(_state().datasets.keys())


def has_datasets() -> bool:
    return bool(_state().datasets)


def active_name() -> Optional[str]:
    return _state().active


def set_active(name: str) -> None:
    if name in _state().datasets:
        _state().active = name


def get_df(name: Optional[str] = None) -> Optional[pd.DataFrame]:
    state = _state()
    name = name or state.active
    entry = state.datasets.get(name) if name else None
    return entry.df if entry else None


def get_mapping(name: Optional[str] = None) -> dict:
    state = _state()
    name = name or state.active
    entry = state.datasets.get(name) if name else None
    return entry.mapping if entry else {}


def set_mapping(name: str, mapping: dict) -> None:
    entry = _state().datasets.get(name)
    if entry:
        entry.mapping = mapping


def rename_dataset(old: str, new: str) -> None:
    state = _state()
    if old in state.datasets and new and new not in state.datasets:
        state.datasets[new] = state.datasets.pop(old)
        if state.active == old:
            state.active = new


def remove_dataset(name: str) -> None:
    state = _state()
    state.datasets.pop(name, None)
    if state.active == name:
        state.active = next(iter(state.datasets), None)


def clear_all() -> None:
    _state().datasets.clear()
    _state().active = None


# --------------------------------------------------------------------------
# Cleaning: apply + undo, with a running log
# --------------------------------------------------------------------------
def apply_transform(name: str, new_df: pd.DataFrame, message: str) -> None:
    entry = _state().datasets.get(name)
    if not entry:
        return
    entry.history.append(entry.df)
    entry.df = new_df
    entry.log.append(message)
    if len(entry.history) > 20:
        entry.history.pop(0)


def undo(name: str) -> bool:
    entry = _state().datasets.get(name)
    if not entry or not entry.history:
        return False
    entry.df = entry.history.pop()
    if entry.log:
        entry.log.append(f"Undid: {entry.log.pop()}")
    return True


def cleaning_log(name: Optional[str] = None) -> list[str]:
    state = _state()
    name = name or state.active
    entry = state.datasets.get(name) if name else None
    return entry.log if entry else []


def can_undo(name: Optional[str] = None) -> bool:
    state = _state()
    name = name or state.active
    entry = state.datasets.get(name) if name else None
    return bool(entry and entry.history)
