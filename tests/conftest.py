# tests/conftest.py

"""
Pytest configuration.

- Redirects StockSimulator data directory to a temporary folder during pytest runs
  to avoid writing into repo-root `data/` (snapshots.csv, transactions.json, etc).
"""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

# --- Silence app logging during pytest --------------------------------------

# Flag so the application knows it is running under tests
os.environ.setdefault("STOCKSIM_TESTING", "1")

# Disable default file logging (logs/app.log) during tests
# (individual tests can still pass log_file explicitly)
os.environ.setdefault("LOG_FILE", "")


# --- Redirect data I/O during tests -----------------------------------------

DATA_DIR_ENV = "STOCKSIM_DATA_DIR"
_created_temp_data_dir = False
_temp_data_dir: Path | None = None

# Only override if the user/CI has not explicitly set it
if DATA_DIR_ENV not in os.environ:
    _created_temp_data_dir = True
    _temp_data_dir = Path(tempfile.mkdtemp(prefix="stocksimulator-data-")).resolve()
    os.environ[DATA_DIR_ENV] = str(_temp_data_dir)


def pytest_sessionfinish(session, exitstatus):
    """Cleanup temp data directory created for this pytest session."""
    _ = (session, exitstatus)
    if _created_temp_data_dir and _temp_data_dir:
        shutil.rmtree(_temp_data_dir, ignore_errors=True)


# vulture: pytest hooks are discovered by name, not by direct calls
_ = pytest_sessionfinish
