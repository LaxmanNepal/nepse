import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from data_quality import freshness_status, validate_stock


def test_valid_stock():
    assert validate_stock({"symbol": "NABIL", "ltp": 1000, "low": 990, "high": 1010, "volume": 10, "turnover": 10000}) == []


def test_rejects_negative_price():
    assert "negative price: NABIL" in validate_stock({"symbol": "NABIL", "ltp": -1})


def test_rejects_invalid_ohlc():
    errors = validate_stock({"symbol": "NABIL", "ltp": 100, "low": 110, "high": 120})
    assert "LTP below low: NABIL" in errors


def test_rejects_high_below_low():
    assert "high below low: NABIL" in validate_stock({"symbol": "NABIL", "ltp": 105, "low": 110, "high": 100})


def test_freshness_bands():
    assert freshness_status(60) == "fresh"
    assert freshness_status(600) == "aging"
    assert freshness_status(1200) == "stale"
    assert freshness_status(None) == "unknown"
