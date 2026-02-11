# src/logger.py

"""
Logging setup for Stock Simulator project.

This module a ingle place to configure logging so the application
has consistent output for debugging and traceability. It configure both:
    - Consol logging (developer/operator visibility)
    - File logging

Usage:
    from src.logger import init_logging_from_env, get_logger

    init_logging_from_env()
    log = get_logger(__name__)
    log.info("Hello from teh app")
"""

from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, Union


DEFAULT_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def _normalize_level(level: str) -> str:
    """Return a valid logging level name; fall back to INFO if invalid."""
    lvl = (level or "INFO").strip().upper()
    return lvl if lvl in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"} else "INFO"


def init_logging(
    *,
    level: str = "INFO",
    log_file: Union[str, Path] = "logs/app.log",
    console: bool = True,
    max_bytes: int = 2_000_000,
    backup_count: int = 5,
) -> None:
    """
    Initialize root logging once (idempotent) with console + rotating file handler.

    - Centralizes configuration in one place (professional-quality requirement).
    - Avoids duplicate handlers if called multiple times (e.g., from main + CLI).
    - Rotates log files to prevent unbounded growth.

    Args:
        level: Default INFO; can be set to DEBUG/INFO/WARNING/ERROR/CRITICAL.
        log_file: Log file path. Parent directories are created if needed.
        console: If True, logs are written to stdout/stderr via StreamHandler.
        max_bytes: Rotation threshold per file in bytes.
        backup_count: Number of rotated log files to keep.
    """
    root = logging.getLogger()
    normalized = _normalize_level(level)

    # Prevent duplicate handlers.
    if getattr(root, "_stocksimulator_logging_configured", False):
        root.setLevel(normalized)  # Allow level to be adjusted on subsequent calls.
        return

    root.setLevel(normalized)
    root.handlers.clear()  # Defensive: ensure no stray handlers remain.

    formatter = logging.Formatter(fmt=DEFAULT_LOG_FORMAT, datefmt=DEFAULT_DATE_FORMAT)

    if console:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        root.addHandler(stream_handler)

    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            filename=log_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

    root.propagate = False
    root._stocksimulator_logging_configured = True  # type: ignore[attr-defined]

    # Emit a first log line so the file is created immediately.
    logging.getLogger("stocksimulator").info(
        "Logging initialized (level=%s, log_file=%s)", normalized, str(log_file)
    )


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Return a named logger (recommended practice).

    Args:
        name: Typically __name__ from the calling module.
    """
    return logging.getLogger(name or "stocksimulator")


def init_logging_from_env(*, default_level: str = "INFO") -> None:
    """
    Convenience initializer that reads LOG_LEVEL from environment variables.

    Args:
        default_level: Used if LOG_LEVEL is not set.
    """
    level = os.getenv("LOG_LEVEL", default_level)
    init_logging(level=level)
