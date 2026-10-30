"""Validate generated NEPSE market data before deployment."""
from __future__ import annotations

import json
import pathlib
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parents[1]
LIVE = ROOT / "data" / "live.json"
INDEX = ROOT / "data" / "index-history.json"
HEALTH = ROOT / "data" / "health.json"

sys.path.insert(0, str(ROOT / "scripts"))
from data_quality import as_float, first_value, freshness_seconds, freshness_status, parse_timestamp, validate_stock  # noqa: E402

errors: list[str] = []


def market_is_open() -> bool:
    npt = datetime.now(ZoneInfo("Asia/Kathmandu"))
    return npt.weekday() in (6, 0, 1, 2, 3) and 11 * 60 <= npt.hour * 60 + npt.minute < 15 * 60


def check_timestamp(label: str, value) -> None:
    if value is not None and parse_timestamp(value) is None:
        errors.append(f"invalid timestamp: {label}")


live: dict = {}
stock_count = 0
source_updated_at = None
freshness_age = None

if not LIVE.exists():
    errors.append("data/live.json is missing")
else:
    try:
        payload = json.loads(LIVE.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            errors.append("data/live.json root must be an object")
            payload = {}
        live = payload

        for field in ("schemaVersion", "updatedAt", "source", "sourceUpdatedAt", "stocks"):
            if field not in payload:
                errors.append(f"live snapshot missing required field: {field}")
        check_timestamp("updatedAt", payload.get("updatedAt"))
        check_timestamp("sourceUpdatedAt", payload.get("sourceUpdatedAt"))
        source_updated_at = payload.get("sourceUpdatedAt")
        freshness_age = freshness_seconds(source_updated_at, payload.get("updatedAt"))

        stocks = payload.get("stocks", [])
        if not isinstance(stocks, list) or not stocks:
            errors.append("data/live.json contains no stocks")
            stocks = []
        stock_count = len(stocks)

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

freshness = freshness_status(freshness_age)
market_open = market_is_open()
if market_open and freshness in {"stale", "unknown"}:
    errors.append(f"market snapshot is {freshness} during market hours")

now = datetime.now(timezone.utc).isoformat()
health = {
    "schemaVersion": 1,
    "status": "unhealthy" if errors else "healthy",
    "generatedAt": now,
    "market": "open" if market_open else "closed",
    "source": live.get("source"),
    "sourceUpdatedAt": source_updated_at,
    "ageSeconds": round(freshness_age, 2) if freshness_age is not None else None,
    "freshness": freshness,
    "stocks": stock_count,
    "validation": "failed" if errors else "passed",
    "errors": errors[:100],
}
HEALTH.write_text(json.dumps(health, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

if errors:
    print("MARKET DATA VALIDATION FAILED")
    for error in errors[:100]:
        print(f"- {error}")
    if len(errors) > 100:
        print(f"- ... and {len(errors) - 100} more")
    sys.exit(1)

print(f"MARKET DATA VALIDATION PASSED ({stock_count} stocks; freshness={freshness})")
