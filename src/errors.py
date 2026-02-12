# src/errors.py

"""
Common domain exceptions for StockSimulator.

Defines controlled error types so the CLI can show friendly messages
without crashing on expected failures.
"""

from __future__ import annotations


class ValidationError(ValueError):
    """Raised when user input is invalid."""


class FileError(RuntimeError):
    """Raised when reading/writing local files fails."""
