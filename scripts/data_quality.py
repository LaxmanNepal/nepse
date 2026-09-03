"""Shared data-quality helpers for the NEPSE Pulse pipeline."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


PRICE_KEYS = ("ltp", "lastTradedPrice", "lastPrice", "price", "close", "currentValue")
CHANGE_KEYS = ("change", "changeValue")
PERCENT_KEYS = ("changePercent", "perChange", "percent", "percentage")
VOLUME_KEYS = ("volume", "quantity", "totalTradedQuantity")
TURNOVER_KEYS = ("turnover", "totalTurnover")


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
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
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


def validate_stock(stock: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    symbol = str(stock.get("symbol") or "").strip().upper()
    label = symbol or "<unknown>"
    if not symbol:
        errors.append("stock without symbol")
        return errors

    numeric_fields = {
        "price": PRICE_KEYS,
        "change": CHANGE_KEYS,
        "changePercent": PERCENT_KEYS,
        "volume": VOLUME_KEYS,
        "turnover": TURNOVER_KEYS,
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
        if label_name in {"price", "volume", "turnover"} and number < 0:
            errors.append(f"negative {label_name}: {label}")

    high = as_float(first_value(stock, ("high", "dayHigh")))
    low = as_float(first_value(stock, ("low", "dayLow")))
    ltp = values.get("price")
    if high is not None and low is not None and high < low:
        errors.append(f"high below low: {label}")
    if ltp is not None and high is not None and ltp > high:
        errors.append(f"LTP above high: {label}")
    if ltp is not None and low is not None and ltp < low:
        errors.append(f"LTP below low: {label}")

    return errors
