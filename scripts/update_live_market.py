#!/usr/bin/env python3
"""Refresh, normalize and validate the static NEPSE market snapshot."""
from __future__ import annotations

import json
import pathlib
import urllib.request
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
BASE = "https://shubhamnpk.github.io/yonepse/data/"
UA = "NEPSE-Pulse/7.0 (+https://apps.laxmannepal.com.np/nepse/)"

import sys
sys.path.insert(0, str(ROOT / "scripts"))
from data_quality import as_float, canonical_stock, first_value, parse_timestamp, validate_stock  # noqa: E402


def fetch(path: str):
    req = urllib.request.Request(BASE + path, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as response:
        return json.loads(response.read().decode("utf-8"))


def write_json(path: pathlib.Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def first(row: dict, *keys):
    return first_value(row, tuple(keys))


def number(value):
    return as_float(value)


def sector_map(raw):
    if isinstance(raw, dict):
        source = raw.get("sectors", raw.get("data", raw))
    else:
        source = raw
    mapping = {}
    if isinstance(source, dict):
        for sector, symbols in source.items():
            if not isinstance(symbols, list):
                continue
            for symbol in symbols:
                mapping[str(symbol).upper()] = str(sector)
    elif isinstance(source, list):
        for row in source:
            if not isinstance(row, dict):
                continue
            symbol = row.get("symbol") or row.get("securitySymbol")
            sector = row.get("sectorName") or row.get("sector") or row.get("indexName")
            if symbol and sector:
                mapping[str(symbol).upper()] = str(sector)
    return mapping


def normalize_stock(row: dict, mapping: dict[str, str]) -> dict:
    return canonical_stock(row, mapping.get(str(first(row, "symbol", "ticker", "securitySymbol") or "").strip().upper(), "Other"))


def main():
    stocks = fetch("market/live.json")
    indices = fetch("market/indices.json")
    summary = fetch("market/summary.json")
    status = fetch("market/status.json")
    ltp_manifest = fetch("ltp/manifest.json")
    sectors_raw = fetch("other/sector_codes.json")
    mapping = sector_map(sectors_raw)

    if not isinstance(stocks, list) or not stocks:
        raise RuntimeError("YONEPSE returned no stock rows")
    if not isinstance(status, (dict, list)):
        raise RuntimeError("YONEPSE returned invalid market status")

    now = datetime.now(timezone.utc).isoformat()
    normalized = [normalize_stock(row, mapping) for row in stocks if isinstance(row, dict)]
    normalized = [row for row in normalized if row["symbol"]]
    if not normalized:
        raise RuntimeError("No valid securities after normalization")

    # Use the newest individual quote timestamp, not status.last_checked (which can lag).
    quote_times = [parse_timestamp(row.get("lastUpdated")) for row in normalized if row.get("lastUpdated")]
    quote_times = [stamp for stamp in quote_times if stamp is not None]
    source_updated_at = max(quote_times).isoformat() if quote_times else None
    if not source_updated_at:
        source_updated_at = status.get("last_checked") if isinstance(status, dict) else None
    if not source_updated_at or parse_timestamp(source_updated_at) is None:
        raise RuntimeError("YONEPSE returned an invalid or missing quote timestamp")

    symbols = [row["symbol"] for row in normalized]
    duplicates = sorted({s for s in symbols if symbols.count(s) > 1})
    if duplicates:
        raise RuntimeError("Duplicate security symbols: " + ", ".join(duplicates[:20]))

    # Quarantine individual bad rows instead of discarding an otherwise usable market snapshot.
    # A single stale/illiquid instrument can occasionally have inconsistent high/low fields.
    valid_rows = []
    rejected = []
    for row in normalized:
        errors = validate_stock(row)
        if errors:
            rejected.extend(errors)
        else:
            valid_rows.append(row)
    rejected_count = len(normalized) - len(valid_rows)
    rejected_ratio = rejected_count / max(1, len(normalized))
    if len(valid_rows) < 200 or rejected_ratio > 0.05:
        raise RuntimeError(
            f"Source data quality too poor: valid={len(valid_rows)}, "
            f"rejected={rejected_count} ({rejected_ratio:.1%}); " + "; ".join(rejected[:20])
        )
    normalized = valid_rows
    if rejected:
        print(f"Quarantined {rejected_count} invalid rows: " + "; ".join(rejected[:10]))

    nepse = next((x for x in indices if isinstance(x, dict) and x.get("index") in ("NEPSE", "NEPSE Index")), None)
    live = {
        "schemaVersion": 1,
        "updatedAt": now,
        "source": "YONEPSE public dataset",
        "sourceUpdatedAt": source_updated_at,
        "market": status,
        "index": nepse,
        "summary": summary,
        "stocks": normalized,
    }

    # Only publish after every stock has passed validation, preserving the last good snapshot on failure.
    write_json(DATA / "live.json", live)
    write_json(DATA / "sectors.json", {"schemaVersion": 1, "updatedAt": now, "source": "YONEPSE", "sectors": mapping})
    write_json(DATA / "market-summary.json", {"schemaVersion": 1, "updatedAt": now, "source": "YONEPSE", "summary": summary})

    # Build per-symbol daily close/volume histories from compact monthly LTP shards.
    # Three recent months provide enough observations for 50-day indicators for liquid names.
    months = ltp_manifest.get("availableMonths", []) if isinstance(ltp_manifest, dict) else []
    months = [str(month) for month in months if isinstance(month, str)]
    recent_months = months[-4:]
    history_by_symbol: dict[str, list[dict]] = {}
    for month in recent_months:
        shard = fetch(f"ltp/monthly/{month}.json")
        dates = shard.get("dates", [])
        series = shard.get("series", {})
        if not isinstance(dates, list) or not isinstance(series, dict):
            print(f"Skipping malformed LTP shard: {month}")
            continue
        for symbol, points in series.items():
            if not isinstance(points, list):
                continue
            bucket = history_by_symbol.setdefault(str(symbol).upper(), [])
            for point in points:
                if not isinstance(point, list) or len(point) < 3:
                    continue
                try:
                    date_index = int(point[0])
                    close = number(point[1])
                    volume = number(point[2])
                    if date_index < 0 or date_index >= len(dates) or close is None or close <= 0:
                        continue
                    bucket.append({"date": dates[date_index], "close": close, "volume": volume or 0})
                except (TypeError, ValueError):
                    continue
    history_dir = DATA / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    for symbol, rows in history_by_symbol.items():
        deduped = {row["date"]: row for row in rows}
        ordered = [deduped[key] for key in sorted(deduped)]
        if ordered:
            write_json(history_dir / f"{symbol}.json", ordered)
    print(f"Built daily history for {len(history_by_symbol)} symbols from {len(recent_months)} monthly shards.")

    history_path = DATA / "index-history.json"
    history = {"schemaVersion": 1, "index": "NEPSE", "updatedAt": now, "points": []}
    if history_path.exists():
        try:
            history = json.loads(history_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    points = history.get("points", []) if isinstance(history, dict) else []
    if not isinstance(points, list):
        points = []
    if isinstance(nepse, dict):
        close = number(first(nepse, "close", "currentValue", "value"))
        if close is not None:
            stamp = nepse.get("generatedTime") or now
            point = {
                "date": str(stamp)[:10],
                "timestamp": stamp,
                "value": close,
                "change": number(nepse.get("change")),
                "percent": number(nepse.get("perChange")),
                "high": number(nepse.get("high")),
                "low": number(nepse.get("low")),
            }
            if not points or points[-1].get("timestamp") != point["timestamp"]:
                points.append(point)
    history["updatedAt"] = now
    history["points"] = points[-5000:]
    write_json(history_path, history)

    print(f"Updated {len(normalized)} securities; sectors={len(mapping)}; source={source_updated_at}")


if __name__ == "__main__":
    main()
