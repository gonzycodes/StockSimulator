import pytest
from src.validators import validate_ticker, validate_positive_float, ValidationError

# --- Ticker Tests (TR-254) ---


def test_validate_ticker_normalization():
    # AC: " aapl " -> normalized to "AAPL"
    assert validate_ticker(" aapl ") == "AAPL"
    assert validate_ticker("TSLA") == "TSLA"


def test_validate_ticker_empty():
    # AC: "" (empty) -> fail
    with pytest.raises(ValidationError):
        validate_ticker("")


def test_validate_ticker_whitespace():
    # AC: "   " (whitespace) -> fail
    with pytest.raises(ValidationError):
        validate_ticker("   ")


# --- Amount Tests (TR-254) ---


def test_validate_float_valid_decimal():
    # AC: "2.5" -> ok (if float is allowed)
    assert validate_positive_float("2.5") == 2.5


def test_validate_float_valid_integer_string():
    # AC: "2" -> ok
    assert validate_positive_float("2") == 2.0


def test_validate_float_invalid_zero():
    # AC: "0" -> fail
    with pytest.raises(ValidationError):
        validate_positive_float("0")


def test_validate_float_invalid_negative():
    # AC: "-1" -> fail
    with pytest.raises(ValidationError):
        validate_positive_float("-1")

    with pytest.raises(ValidationError):
        validate_positive_float("-5.5")


def test_validate_float_invalid_text():
    # AC: "abc" -> fail
    with pytest.raises(ValidationError):
        validate_positive_float("abc")
