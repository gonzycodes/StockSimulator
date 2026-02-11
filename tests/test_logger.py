# tests/test_logger.py

"""
Basic tests for logging initialization.

These tests validate that:
- init_logging does not crash
- initialization is idempotent (no duplicate handlers)
- the log file is created
"""

import logging
from pathlib import Path

from src.logger import init_logging, get_logger


def test_init_logging_is_idempotent(tmp_path: Path) -> None:
    """
    Ensure init_logging can be called multiple times without duplicating handlers.
    """
    log_file = tmp_path / "app.log"

    init_logging(level="INFO", log_file=log_file)
    get_logger(__name__).info("test line 1")

    init_logging(level="DEBUG", log_file=log_file)  # Should not add extra handlers
    get_logger(__name__).debug("test line 2")

    root = logging.getLogger()
    assert root.level == logging.DEBUG
    assert log_file.exists()

    # Default configuration: console + file handler = 2 handlers
    assert len(root.handlers) == 2
