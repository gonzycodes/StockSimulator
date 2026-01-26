# tests/conftest.py

"""
Pytest configuration.

Ensures the repository root is on sys.path so imports like `from src...` work
when running tests locally and in CI.
"""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

