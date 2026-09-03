import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from data_quality import freshness_status, validate_stock


class DataQualityTests(unittest.TestCase):
    def test_valid_stock(self):
        self.assertEqual(
            validate_stock({"symbol": "NABIL", "ltp": 1000, "low": 990, "high": 1010, "volume": 10, "turnover": 10000}),
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

    def test_freshness_bands(self):
        self.assertEqual(freshness_status(60), "fresh")
        self.assertEqual(freshness_status(600), "aging")
        self.assertEqual(freshness_status(1200), "stale")
        self.assertEqual(freshness_status(None), "unknown")


if __name__ == "__main__":
    unittest.main()
