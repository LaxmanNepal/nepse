"""Validate generated NEPSE market data before deployment."""
from __future__ import annotations

import json
import pathlib
import sys
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
LIVE = ROOT / "data" / "live.json"
INDEX = ROOT / "data" / "index-history.json"

sys.path.insert(0, str(ROOT / "scripts"))
from data_quality import as_float, first_value, parse_timestamp, validate_stock  # noqa: E402

errors: list[str] = []


def check_timestamp(label: str, value) -> None:
    if value is not None and parse_timestamp(value) is None:
        errors.append(f"invalid timestamp: {label}")


if not LIVE.exists():
    errors.append("data/live.json is missing")
else:
    try:
        payload = json.loads(LIVE.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            errors.append("data/live.json root must be an object")
            payload = {}

        for field in ("updatedAt", "source", "stocks"):
            if field not in payload:
                errors.append(f"live snapshot missing required field: {field}")
        check_timestamp("updatedAt", payload.get("updatedAt"))

        stocks = payload.get("stocks", [])
        if not isinstance(stocks, list) or not stocks:
            errors.append("data/live.json contains no stocks")
            stocks = []

        symbols: set[str] = set()
        for stock in stocks:
            if not isinstance(stock, dict):
                errors.append("stock row is not an object")
                continue
            symbol = str(stock.get("symbol") or stock.get("ticker") or stock.get("securitySymbol") or "").strip().upper()
            if symbol in symbols:
                errors.append(f"duplicate symbol: {symbol}")
            if symbol:
                symbols.add(symbol)
            errors.extend(validate_stock(stock))
            check_timestamp(f"{symbol}.last_updated", stock.get("last_updated") or stock.get("lastUpdated"))

        index = payload.get("index")
        if index is not None:
            if not isinstance(index, dict):
                errors.append("live index is not an object")
            else:
                close = as_float(first_value(index, ("close", "currentValue", "value")))
                if close is not None and close < 0:
                    errors.append("negative NEPSE index value")
                check_timestamp("index.generatedTime", index.get("generatedTime"))

        summary = payload.get("summary")
        if summary is not None and not isinstance(summary, (dict, list)):
            errors.append("live summary must be an object or list")
    except json.JSONDecodeError as exc:
        errors.append(f"invalid live.json: {exc}")

if INDEX.exists():
    try:
        history = json.loads(INDEX.read_text(encoding="utf-8"))
        if not isinstance(history, dict):
            errors.append("index-history root is not an object")
        elif not isinstance(history.get("points", []), list):
            errors.append("index-history points is not a list")
    except json.JSONDecodeError as exc:
        errors.append(f"invalid index-history.json: {exc}")

if errors:
    print("MARKET DATA VALIDATION FAILED")
    for error in errors[:100]:
        print(f"- {error}")
    if len(errors) > 100:
        print(f"- ... and {len(errors) - 100} more")
    sys.exit(1)

print("MARKET DATA VALIDATION PASSED")
