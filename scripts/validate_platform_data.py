#!/usr/bin/env python3
"""Validate NEPSE Pulse canonical JSON snapshots without modifying data."""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    "data/live.json", "data/status.json", "data/sectors.json", "data/ipos.json",
    "data/news.json", "data/news-sources.json", "data/history/manifest.json",
    "data/companies.json", "data/index-history.json",
]

def read_json(rel: str):
    path = ROOT / rel
    if not path.exists():
        print(f"INFO missing optional dataset: {rel}")
        return None
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR {rel}: {exc}")
        raise

def unwrap(value):
    if isinstance(value, dict) and isinstance(value.get("content"), str):
        try:
            return json.loads(value["content"])
        except json.JSONDecodeError:
            return value
    return value

def stock_rows(value):
    value = unwrap(value)
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        for key in ("stocks", "data", "items", "rows", "companies"):
            if isinstance(value.get(key), list):
                return value[key]
    return []

def main() -> int:
    failed = False
    for rel in FILES:
        try:
            read_json(rel)
        except Exception:
            failed = True

    live = unwrap(read_json("data/live.json"))
    stocks = stock_rows(live)
    if live is None:
        pass
    elif not isinstance(live, (dict, list)):
        print("ERROR data/live.json: expected object or array")
        failed = True
    else:
        bad = [i for i, item in enumerate(stocks) if not isinstance(item, dict)]
        if bad:
            print(f"ERROR data/live.json: non-object stock entries at indexes {bad[:10]}")
            failed = True
        symbols = [str(s.get("symbol") or s.get("ticker") or "").strip().upper() for s in stocks if isinstance(s, dict)]
        if not stocks:
            print("WARNING data/live.json: no stock records found")
        if any(not s for s in symbols):
            print(f"WARNING data/live.json: {sum(not s for s in symbols)} records have no symbol")
        duplicates = len(symbols) - len(set(s for s in symbols if s))
        if duplicates:
            print(f"WARNING data/live.json: {duplicates} duplicate symbol(s)")
        print(f"OK data/live.json: {len(stocks)} stock records")

    sectors = unwrap(read_json("data/sectors.json"))
    if sectors is not None:
        sector_rows = sectors.get("sectors") if isinstance(sectors, dict) else sectors
        if sector_rows is not None and not isinstance(sector_rows, list):
            print("ERROR data/sectors.json: 'sectors' must be an array")
            failed = True
        elif isinstance(sector_rows, list):
            bad = [i for i, item in enumerate(sector_rows) if not isinstance(item, dict)]
            if bad:
                print(f"ERROR data/sectors.json: invalid entries at indexes {bad[:10]}")
                failed = True
            print(f"OK data/sectors.json: {len(sector_rows)} sector summaries")

    companies = unwrap(read_json("data/companies.json"))
    if companies is not None:
        mapping = companies.get("companies") if isinstance(companies, dict) else None
        if mapping is not None and not isinstance(mapping, dict):
            print("ERROR data/companies.json: 'companies' must be an object")
            failed = True
        elif isinstance(mapping, dict):
            print(f"OK data/companies.json: {len(mapping)} company records")

    index_history = unwrap(read_json("data/index-history.json"))
    if index_history is not None:
        points = index_history.get("points") if isinstance(index_history, dict) else None
        if points is not None and not isinstance(points, list):
            print("ERROR data/index-history.json: 'points' must be an array")
            failed = True
        elif isinstance(points, list):
            print(f"OK data/index-history.json: {len(points)} index points")

    if not failed:
        print("Platform data validation passed (missing optional files are informational).")
        return 0
    print("Platform data validation failed.")
    return 1

if __name__ == "__main__":
    sys.exit(main())
