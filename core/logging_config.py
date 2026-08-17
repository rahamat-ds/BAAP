"""Centralized logging configuration.

Call :func:`get_logger` from any module to obtain a correctly configured
logger. Configuration happens exactly once per process.
"""
from __future__ import annotations

import logging
import sys
from functools import lru_cache

from config import settings

_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATEFMT = "%Y-%m-%d %H:%M:%S"


@lru_cache(maxsize=1)
def _configure_root() -> None:
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(_FORMAT, datefmt=_DATEFMT))

    root = logging.getLogger("insightflow")
    root.setLevel(level)
    root.propagate = False
    if not root.handlers:
        root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Return a module-scoped logger under the ``insightflow`` namespace."""
    _configure_root()
    return logging.getLogger(f"insightflow.{name}")
