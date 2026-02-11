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
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, Union


DEFAULT_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
TEST_MODE_ENV = "STOCKSIM_TESTING"
LOG_FILE_ENV = "LOG_FILE"
DEFAULT_LOG_FILE = "logs/app.log"
_DISABLED_LOG_VALUES = {"", "0", "false", "off", "none", "null"}


def _normalize_level(level: str) -> str:
    """Return a valid logging level name; fall back to INFO if invalid."""
    lvl = (level or "INFO").strip().upper()
    return lvl if lvl in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"} else "INFO"


def init_logging(
    *,
    level: str = "INFO",
    log_file: Union[str, Path, None] = DEFAULT_LOG_FILE,
    console: bool | None = None,
    max_bytes: int = 2_000_000,
    backup_count: int = 5,
) -> None:
    """
    Initialize root logging (idempotent) with optional console + rotating file handler.

    Behavior:
    - No duplicate handlers (reconfigures cleanly on every call)
    - During pytest (STOCKSIM_TESTING=1): console is disabled by default
    - During pytest: default file logging (logs/app.log) is disabled
    - LOG_FILE env can override the default log file; LOG_FILE="" disables it
      (explicit log_file passed by a test is still respected)
    """
    test_mode = os.getenv(TEST_MODE_ENV, "").strip() == "1"

    # Decide console default: OFF in tests, ON otherwise
    if console is None:
        console = not test_mode

    # Normalize level
    root = logging.getLogger()
    normalized = _normalize_level(level)
    root.setLevel(normalized)

    # Determine whether caller is using the default log file
    log_file_str = "" if log_file is None else str(log_file).replace("\\", "/")
    using_default_log_file = log_file_str == DEFAULT_LOG_FILE

    # If using default log file, allow env override (or disable)
    if using_default_log_file:
        env_log_file = os.getenv(LOG_FILE_ENV)
        if test_mode:
            # Never write to default app log during tests
            log_file = None

        if env_log_file is not None:
            v = env_log_file.strip()
            if v.lower() in _DISABLED_LOG_VALUES:
                log_file = None
            elif v:
                log_file = v

    # Always reset handlers to avoid stale/closed streams and duplicates
    for h in list(root.handlers):
        root.removeHandler(h)
        try:
            h.close()
        except Exception:
            pass

    formatter = logging.Formatter(fmt=DEFAULT_LOG_FORMAT, datefmt=DEFAULT_DATE_FORMAT)

    if console:
        stream_handler = logging.StreamHandler(stream=sys.stderr)
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
