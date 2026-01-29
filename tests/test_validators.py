import pytest
from src.validators import normalize_ticker, validate_ticker, validate_positive_float, ValidationError

# Tests for ticker

def test_normalize_ticker_basic():
    # En vanlig ticker ska bli versaler.
    assert normalize_ticker(" aapl ") == "AAPL"
    assert normalize_ticker("GOOGL") == "GOOGL"
    assert normalize_ticker("") == ""
    assert normalize_ticker("  ") == ""
    
def test_normalize_ticker_with_messy_input():
    # Mellanslag ska städas bort.
    assert normalize_ticker(" msft$ ") == "MSFT$"
    assert normalize_ticker("!tsla") == "!TSLA"
    
def test_validate_ticker_empty():
    # Tomma tickers ska ge ValidationError.
    with pytest.raises(ValidationError):
        validate_ticker("")
        
    with pytest.raises(ValidationError):
        validate_ticker("   ")
        
def test_validate_float_valid():
    # Giltiga positiva float-värden ska returneras korrekt.
    result = validate_positive_float("10.5")
    assert result == 10.5
    assert isinstance(result, float)
    
def test_validate_float_invalid_non_numeric():
    # Icke-numeriska värden ska ge ValidationError.
    with pytest.raises(ValidationError):
        validate_positive_float("abc")

def test_validate_float_invalid_negative():
    # Negativa värden ska ge ValidationError.
    with pytest.raises(ValidationError):
        validate_positive_float("-5")

def test_validate_float_invalid_zero():
    # Noll ska ge ValidationError.
    with pytest.raises(ValidationError):
        validate_positive_float("0")