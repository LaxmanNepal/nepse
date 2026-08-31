#!/usr/bin/env python3
"""Refresh the local NEPSE snapshot from the public YONEPSE datasets.

The dashboard is static, so GitHub Actions must materialize a fresh snapshot
into data/ for the site to remain fast and usable without a backend.
"""
from __future__ import annotations

import json
import pathlib
import urllib.request
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
BASE = "https://shubhamnpk.github.io/yonepse/data/"
UA = "NEPSE-Pulse/6.0 (+https://apps.laxmannepal.com.np/Nepse)"


def fetch(path: str):
    req = urllib.request.Request(BASE + path, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as response:
        return json.loads(response.read().decode("utf-8"))


def write_json(path: pathlib.Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def sector_map(raw):
    # YONEPSE publishes {sector: [symbols]} and may add metadata later.
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


def main():
    stocks = fetch("nepse_data.json")
    indices = fetch("market/indices.json")
    summary = fetch("market/summary.json")
    status = fetch("market/status.json")
    sectors_raw = fetch("other/sector_codes.json")
    mapping = sector_map(sectors_raw)

    if not isinstance(stocks, list) or not stocks:
        raise RuntimeError("YONEPSE returned no stock rows")

    now = datetime.now(timezone.utc).isoformat()
    normalized = []
    for row in stocks:
        if not isinstance(row, dict) or not row.get("symbol"):
            continue
        item = dict(row)
        symbol = str(item["symbol"]).upper()
        item["symbol"] = symbol
        item["sector"] = (
            item.get("sector") or item.get("sectorName") or mapping.get(symbol) or "Other"
        )
        normalized.append(item)

    live = {
        "updatedAt": now,
        "source": "YONEPSE public dataset",
        "sourceUpdatedAt": status.get("last_checked") if isinstance(status, dict) else None,
        "market": status,
        "index": next((x for x in indices if isinstance(x, dict) and x.get("index") == "NEPSE"), None),
        "summary": summary,
        "stocks": normalized,
    }

    write_json(DATA / "live.json", live)
    write_json(DATA / "sectors.json", {"updatedAt": now, "sectors": mapping})
    write_json(DATA / "market-summary.json", {"updatedAt": now, "source": "YONEPSE", "summary": summary})

    nepse = live["index"]
    history_path = DATA / "index-history.json"
    history = {"index": "NEPSE", "updatedAt": now, "points": []}
    if history_path.exists():
        try:
            history = json.loads(history_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    points = history.get("points", []) if isinstance(history, dict) else []
    if not isinstance(points, list):
        points = []
    if isinstance(nepse, dict) and nepse.get("close") is not None:
        stamp = nepse.get("generatedTime") or now
        point = {
            "date": str(stamp)[:10],
            "timestamp": stamp,
            "value": nepse.get("close", nepse.get("currentValue")),
            "change": nepse.get("change"),
            "percent": nepse.get("perChange"),
            "high": nepse.get("high"),
            "low": nepse.get("low"),
        }
        if not points or points[-1].get("timestamp") != point["timestamp"]:
            points.append(point)
    history["updatedAt"] = now
    history["points"] = points[-5000:]
    write_json(history_path, history)

    print(f"Updated {len(normalized)} securities; sectors={len(mapping)}; source={status.get('last_checked') if isinstance(status, dict) else 'unknown'}")


if __name__ == "__main__":
    main()
