"""
Central validation logic for user inputs.
"""

from src.errors import ValidationError


def normalize_ticker(raw_ticker: str) -> str:
    """
    Cleans up a ticker symbol string.
    Strips whitespace and converts to uppercase.
    """
    if not raw_ticker:
        return ""

    return raw_ticker.strip().upper()


def validate_ticker(ticker: str) -> str:
    """
    Validates that a ticker is not empty after normalization.
    Returns the clean ticker or raises ValidationError.
    """
    clean_ticker = normalize_ticker(ticker)

    if not clean_ticker:
        raise ValidationError("Ticker symbol cannot be empty.")

    return clean_ticker


def validate_positive_float(raw_value: str) -> float:
    """
    Converts a string to a positive float.
    Raises ValidationError if the input is not a number or <= 0.
    """
    try:
        value = float(raw_value)
    except ValueError:
        raise ValidationError(f"Value '{raw_value}' is not a valid number.")

    if value <= 0:
        raise ValidationError(f"Value '{raw_value}' must be greater than zero.")

    return value


def validate_positive_number(value: float | int, *, name: str = "value") -> float:
    """
    Validates that a numeric value is a number > 0.
    Raises ValidationError on invalid input.
    """
    try:
        num = float(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{name} must be a number.")

    if num <= 0:
        raise ValidationError(f"{name} must be greater than zero.")

    return num
