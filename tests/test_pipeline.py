"""Regression tests for NEPSE data integrity and fail-closed signals."""
import json, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import data_quality, generate_ai_signals
class DataQualityTests(unittest.TestCase):
    def test_non_finite_numbers_are_missing(self):
        for value in ("NaN", "Infinity", "-Infinity", float("nan"), float("inf")):
            self.assertIsNone(data_quality.as_float(value))
    def test_normal_number_is_parsed(self):
        self.assertEqual(data_quality.as_float("1,234.50"), 1234.5)
    def test_high_low_inconsistency_is_rejected(self):
        row = {"symbol":"TEST","ltp":100,"previousClose":99,"change":1,"changePercent":1.01,"high":90,"low":95}
        self.assertTrue(any("high below low" in e for e in data_quality.validate_stock(row)))
    def test_change_mismatch_is_rejected(self):
        row = {"symbol":"TEST","ltp":101,"previousClose":100,"change":9,"changePercent":9,"high":102,"low":99}
        self.assertTrue(any("change mismatch" in e for e in data_quality.validate_stock(row)))
class SignalSafetyTests(unittest.TestCase):
    def test_signal_generator_locks_unverified_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            live, out = Path(tmp)/"live.json", Path(tmp)/"signals.json"
            live.write_text(json.dumps({"sourceVerification":{"status":"unverified"},"tradeSignalsEnabled":False,"stocks":[{"symbol":"TEST","ltp":100}]}), encoding="utf-8")
            with patch.object(generate_ai_signals,"LIVE_PATH",live), patch.object(generate_ai_signals,"OUT_PATH",out):
                generate_ai_signals.main()
            result = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(result["status"],"LOCKED_UNVERIFIED_SOURCE")
            self.assertEqual(result["signals"],[])
    def test_missing_symbol_timestamp_is_not_scored(self):
        stock = {"symbol":"TEST","quoteStatus":"available","listingStatus":"A","ltp":100,"previousClose":99,"high":101,"low":98,"volume":1000,"turnover":1000000,"changePercent":1}
        self.assertIsNone(generate_ai_signals.score_stock(stock))
if __name__ == "__main__": unittest.main()
