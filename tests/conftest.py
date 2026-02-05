# tests/conftest.py

"""
Pytest configuration.

- Ensures the repository root is on sys.path so imports like `from src...` work.
- Redirects StockSimulator data directory to a temporary folder during pytest runs
  to avoid writing into repo-root `data/` (snapshots.csv, transactions.json, etc).
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

# --- Redirect data I/O during tests -----------------------------------------

DATA_DIR_ENV = "STOCKSIM_DATA_DIR"
_created_temp_data_dir = False
_temp_data_dir: Path | None = None

# Only override if the user/CI has not explicitly set it
if DATA_DIR_ENV not in os.environ:
    _created_temp_data_dir = True
    _temp_data_dir = Path(tempfile.mkdtemp(prefix="stocksimulator-data-")).resolve()
    os.environ[DATA_DIR_ENV] = str(_temp_data_dir)

# --- Ensure repo root is importable ------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))


def pytest_sessionfinish(session, exitstatus):  # noqa: ARG001
    """Cleanup temp data directory created for this pytest session."""
    if _created_temp_data_dir and _temp_data_dir:
        shutil.rmtree(_temp_data_dir, ignore_errors=True)
