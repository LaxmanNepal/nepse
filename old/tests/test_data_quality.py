import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from data_quality import canonical_stock, freshness_status, parse_timestamp, validate_stock


class DataQualityTests(unittest.TestCase):
    def test_canonical_stock_schema(self):
        stock = canonical_stock({
            "securitySymbol": " nabil ",
            "securityName": "Nabil Bank",
            "lastTradedPrice": "1,000",
            "previous_close": "990",
            "change": "10",
            "percent_change": "1.01",
        }, "Banking")
        self.assertEqual(stock["symbol"], "NABIL")
        self.assertEqual(stock["sector"], "Banking")
        self.assertEqual(stock["ltp"], 1000.0)
        self.assertEqual(stock["previousClose"], 990.0)

    def test_valid_stock(self):
        self.assertEqual(
            validate_stock({
                "symbol": "NABIL", "ltp": 1000, "previousClose": 990,
                "change": 10, "changePercent": 1.01,
                "low": 990, "high": 1010, "volume": 10, "turnover": 10000,
            }),
            [],
        )

    def test_rejects_negative_price(self):
        self.assertIn("negative price: NABIL", validate_stock({"symbol": "NABIL", "ltp": -1}))

    def test_rejects_invalid_ohlc(self):
        errors = validate_stock({"symbol": "NABIL", "ltp": 100, "low": 110, "high": 120})
        self.assertIn("LTP below low: NABIL", errors)

    def test_rejects_high_below_low(self):
        self.assertIn(
            "high below low: NABIL",
            validate_stock({"symbol": "NABIL", "ltp": 105, "low": 110, "high": 100}),
        )

    def test_rejects_change_mismatch(self):
        self.assertIn(
            "change mismatch: NABIL",
            validate_stock({"symbol": "NABIL", "ltp": 1000, "previousClose": 990, "change": 5}),
        )

    def test_rejects_invalid_timestamp(self):
        self.assertIn(
            "invalid timestamp: NABIL.lastUpdated",
            validate_stock({"symbol": "NABIL", "ltp": 100, "lastUpdated": "not-a-date"}),
        )

    def test_parses_naive_npt_timestamp(self):
        self.assertIsNotNone(parse_timestamp("2026-08-21 14:59:59.123456"))

    def test_freshness_bands(self):
        self.assertEqual(freshness_status(60), "fresh")
        self.assertEqual(freshness_status(600), "aging")
        self.assertEqual(freshness_status(1200), "stale")
        self.assertEqual(freshness_status(None), "unknown")


if __name__ == "__main__":
    unittest.main()
