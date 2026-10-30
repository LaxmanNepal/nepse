"""Shared normalization and data-quality helpers for the NEPSE pipeline."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

NPT = ZoneInfo("Asia/Kathmandu")
PRICE_KEYS = ("ltp", "lastTradedPrice", "lastPrice", "price", "close", "currentValue")
PREVIOUS_CLOSE_KEYS = ("previousClose", "previous_close", "prevClose")
CHANGE_KEYS = ("change", "changeValue")
PERCENT_KEYS = ("changePercent", "percent_change", "perChange", "percent", "percentage")
VOLUME_KEYS = ("volume", "quantity", "totalTradedQuantity")
TURNOVER_KEYS = ("turnover", "totalTurnover")
TRADES_KEYS = ("trades", "totalTrades")
MARKET_CAP_KEYS = ("marketCap", "market_cap")


def first_value(row: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in row and row[key] not in (None, ""):
            return row[key]
    return None


def as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        number = float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None
    return number


def parse_timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed = datetime.strptime(text, "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            try:
                parsed = datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=NPT)
    return parsed.astimezone(timezone.utc)


def freshness_seconds(source_updated_at: Any, generated_at: Any) -> float | None:
    source = parse_timestamp(source_updated_at)
    generated = parse_timestamp(generated_at)
    if source is None or generated is None:
        return None
    return max(0.0, (generated - source).total_seconds())


def freshness_status(age_seconds: float | None) -> str:
    if age_seconds is None:
        return "unknown"
    if age_seconds <= 300:
        return "fresh"
    if age_seconds <= 900:
        return "aging"
    return "stale"


def canonical_stock(row: dict[str, Any], sector: str = "Other") -> dict[str, Any]:
    """Map a source row into the stable public stock schema."""
    symbol = str(first_value(row, ("symbol", "ticker", "securitySymbol")) or "").strip().upper()
    return {
        "symbol": symbol,
        "name": first_value(row, ("name", "securityName", "companyName")),
        "sector": first_value(row, ("sector", "sectorName")) or sector,
        "ltp": as_float(first_value(row, PRICE_KEYS)),
        "previousClose": as_float(first_value(row, PREVIOUS_CLOSE_KEYS)),
        "change": as_float(first_value(row, CHANGE_KEYS)),
        "changePercent": as_float(first_value(row, PERCENT_KEYS)),
        "open": as_float(first_value(row, ("open", "openPrice"))),
        "high": as_float(first_value(row, ("high", "dayHigh"))),
        "low": as_float(first_value(row, ("low", "dayLow"))),
        "volume": as_float(first_value(row, VOLUME_KEYS)),
        "turnover": as_float(first_value(row, TURNOVER_KEYS)),
        "trades": as_float(first_value(row, TRADES_KEYS)),
        "marketCap": as_float(first_value(row, MARKET_CAP_KEYS)),
        "lastUpdated": first_value(row, ("lastUpdated", "last_updated", "generatedTime")),
    }


def _approx(actual: float, expected: float, tolerance: float = 0.02) -> bool:
    return abs(actual - expected) <= tolerance + abs(expected) * 0.002


def validate_stock(stock: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    symbol = str(stock.get("symbol") or "").strip().upper()
    label = symbol or "<unknown>"
    if not symbol:
        errors.append("stock without symbol")
        return errors

    numeric_fields = {
        "price": PRICE_KEYS,
        "previousClose": PREVIOUS_CLOSE_KEYS,
        "change": CHANGE_KEYS,
        "changePercent": PERCENT_KEYS,
        "volume": VOLUME_KEYS,
        "turnover": TURNOVER_KEYS,
        "trades": TRADES_KEYS,
        "marketCap": MARKET_CAP_KEYS,
    }
    values: dict[str, float | None] = {}
    for label_name, keys in numeric_fields.items():
        raw = first_value(stock, keys)
        if raw is None:
            values[label_name] = None
            continue
        number = as_float(raw)
        if number is None:
            errors.append(f"invalid {label_name}: {label}")
            continue
        values[label_name] = number
        if label_name != "change" and number < 0:
            errors.append(f"negative {label_name}: {label}")

    high = as_float(first_value(stock, ("high", "dayHigh")))
    low = as_float(first_value(stock, ("low", "dayLow")))
    opening = as_float(first_value(stock, ("open", "openPrice")))
    ltp = values.get("price")
    previous = values.get("previousClose")
    change = values.get("change")
    percent = values.get("changePercent")

    if high is not None and low is not None and high < low:
        errors.append(f"high below low: {label}")
    if ltp is not None and high is not None and ltp > high:
        errors.append(f"LTP above high: {label}")
    if ltp is not None and low is not None and ltp < low:
        errors.append(f"LTP below low: {label}")
    if opening is not None and high is not None and opening > high:
        errors.append(f"open above high: {label}")
    if opening is not None and low is not None and opening < low:
        errors.append(f"open below low: {label}")

    if previous is not None and ltp is not None and change is not None:
        if not _approx(change, ltp - previous):
            errors.append(f"change mismatch: {label}")
    if previous is not None and previous > 0 and change is not None and percent is not None:
        expected_percent = change / previous * 100
        if not _approx(percent, expected_percent, tolerance=0.03):
            errors.append(f"changePercent mismatch: {label}")

    timestamp = first_value(stock, ("lastUpdated", "last_updated", "generatedTime"))
    if timestamp is not None and parse_timestamp(timestamp) is None:
        errors.append(f"invalid timestamp: {label}.lastUpdated")
    return errors
