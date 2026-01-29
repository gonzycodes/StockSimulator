import pytest
from src.validators import normalize_ticker, validate_ticker, validate_positive_float, ValidationError

def test_normalize_ticker_basic():
    # Standard tickers should be normalized to uppercase.
    assert normalize_ticker(" aapl ") == "AAPL"
    assert normalize_ticker("GOOGL") == "GOOGL"
    assert normalize_ticker("") == ""
    assert normalize_ticker("  ") == ""
    
def test_normalize_ticker_with_messy_input():
    # Surrounding whitespace should be stripped.
    assert normalize_ticker(" msft$ ") == "MSFT$"
    assert normalize_ticker("!tsla") == "!TSLA"
    
def test_validate_ticker_empty():
    # Empty tickers should raise a ValidationError.
    with pytest.raises(ValidationError):
        validate_ticker("")
        
    with pytest.raises(ValidationError):
        validate_ticker("   ")
        
def test_validate_float_valid():
    # Valid positive floats should be returned correctly.
    result = validate_positive_float("10.5")
    assert result == 10.5
    assert isinstance(result, float)
    
def test_validate_float_invalid_non_numeric():
    # Non-numeric values should raise a ValidationError.
    with pytest.raises(ValidationError):
        validate_positive_float("abc")

def test_validate_float_invalid_negative():
    # Negative values should raise a ValidationError.
    with pytest.raises(ValidationError):
        validate_positive_float("-5")

def test_validate_float_invalid_zero():
    # Zero should raise a ValidationError.
    with pytest.raises(ValidationError):
        validate_positive_float("0")
