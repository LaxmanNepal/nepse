#!/usr/bin/env python3
"""Validate the canonical NEPSE Pulse JSON snapshots without modifying data."""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    "data/live.json",
    "data/status.json",
    "data/sectors.json",
    "data/ipos.json",
    "data/news.json",
    "data/news-sources.json",
    "data/history/manifest.json",
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

def main() -> int:
    failed = False
    for rel in FILES:
        try:
            read_json(rel)
        except Exception:
            failed = True
    live = read_json("data/live.json")
    if isinstance(live, dict):
        stocks = live.get("stocks", live.get("data", []))
        if stocks is not None and not isinstance(stocks, list):
            print("ERROR data/live.json: expected 'stocks' or 'data' to be an array")
            failed = True
        elif isinstance(stocks, list):
            missing = [i for i, item in enumerate(stocks) if not isinstance(item, dict)]
            if missing:
                print(f"ERROR data/live.json: non-object stock entries at indexes {missing[:10]}")
                failed = True
            else:
                symbols = [str(s.get("symbol") or s.get("ticker") or "").strip() for s in stocks]
                empty = sum(not symbol for symbol in symbols)
                if empty:
                    print(f"WARNING data/live.json: {empty} stock records have no symbol")
                duplicates = len([s for s in symbols if s]) - len(set(s for s in symbols if s))
                if duplicates:
                    print(f"WARNING data/live.json: {duplicates} duplicate symbol(s)")
                print(f"OK data/live.json: {len(stocks)} stock records")
    elif live is not None and not isinstance(live, list):
        print("ERROR data/live.json: expected object or array")
        failed = True
    if not failed:
        print("Platform data validation passed (missing optional files are informational).")
        return 0
    print("Platform data validation failed.")
    return 1

if __name__ == "__main__":
    sys.exit(main())
