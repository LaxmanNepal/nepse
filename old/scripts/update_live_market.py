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
    stocks = fetch("nepse_data.json")
    indices = fetch("market/indices.json")
    summary = fetch("market/summary.json")
    status = fetch("market/status.json")
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

    source_updated_at = status.get("last_checked") if isinstance(status, dict) else None
    if not source_updated_at or parse_timestamp(source_updated_at) is None:
        raise RuntimeError("YONEPSE returned an invalid or missing source timestamp")

    symbols = [row["symbol"] for row in normalized]
    duplicates = sorted({s for s in symbols if symbols.count(s) > 1})
    if duplicates:
        raise RuntimeError("Duplicate security symbols: " + ", ".join(duplicates[:20]))

    quality_errors = []
    for row in normalized:
        quality_errors.extend(validate_stock(row))
    if quality_errors:
        raise RuntimeError("Source data failed validation: " + "; ".join(quality_errors[:20]))

    nepse = next((x for x in indices if isinstance(x, dict) and x.get("index") == "NEPSE"), None)
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
