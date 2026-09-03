#!/usr/bin/env python3
"""Refresh and normalize the static NEPSE market snapshot."""
from __future__ import annotations

import json
import pathlib
import urllib.request
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
BASE = "https://shubhamnpk.github.io/yonepse/data/"
UA = "NEPSE-Pulse/7.0 (+https://apps.laxmannepal.com.np/nepse/)"


def fetch(path: str):
    req = urllib.request.Request(BASE + path, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as response:
        return json.loads(response.read().decode("utf-8"))


def write_json(path: pathlib.Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def first(row: dict, *keys):
    for key in keys:
        if row.get(key) not in (None, ""):
            return row[key]
    return None


def number(value):
    if value in (None, ""):
        return None
    try:
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None


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
    symbol = str(first(row, "symbol", "ticker", "securitySymbol") or "").strip().upper()
    return {
        "symbol": symbol,
        "name": first(row, "name", "securityName", "companyName"),
        "sector": first(row, "sector", "sectorName") or mapping.get(symbol) or "Other",
        "ltp": number(first(row, "ltp", "lastTradedPrice", "lastPrice", "price")),
        "previousClose": number(first(row, "previousClose", "previous_close", "prevClose")),
        "change": number(first(row, "change", "changeValue")),
        "changePercent": number(first(row, "changePercent", "percent_change", "perChange", "percentage")),
        "open": number(first(row, "open", "openPrice")),
        "high": number(first(row, "high", "dayHigh")),
        "low": number(first(row, "low", "dayLow")),
        "volume": number(first(row, "volume", "quantity", "totalTradedQuantity")),
        "turnover": number(first(row, "turnover", "totalTurnover")),
        "trades": number(first(row, "trades", "totalTrades")),
        "marketCap": number(first(row, "marketCap", "market_cap")),
        "lastUpdated": first(row, "lastUpdated", "last_updated", "generatedTime"),
    }


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

    write_json(DATA / "live.json", live)
    write_json(DATA / "sectors.json", {"schemaVersion": 1, "updatedAt": now, "source": "YONEPSE", "sectors": mapping})
    write_json(DATA / "market-summary.json", {"schemaVersion": 1, "updatedAt": now, "source": "YONEPSE", "summary": summary})
    write_json(DATA / "health.json", {
        "schemaVersion": 1,
        "status": "ok",
        "generatedAt": now,
        "source": live["source"],
        "sourceUpdatedAt": source_updated_at,
        "stocks": len(normalized),
        "validation": "pending",
    })

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

    print(f"Updated {len(normalized)} securities; sectors={len(mapping)}; source={source_updated_at or 'unknown'}")


if __name__ == "__main__":
    main()
