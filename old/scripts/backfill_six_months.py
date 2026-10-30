#!/usr/bin/env python3
"""Download the previous six calendar months of NEPSE LTP history.

The public YONEPSE monthly shards are used as the machine-readable source.
Each shard contains every symbol's daily LTP/volume/turnover/trades series.
"""
from __future__ import annotations
import json
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "history" / "ltp"
BASE = "https://raw.githubusercontent.com/Shubhamnpk/yonepse/main/data/ltp/monthly"
TODAY = date.today()

# Current month + five preceding months = six months of rolling history.
def months_back(year: int, month: int, n: int):
    idx = year * 12 + (month - 1) - n
    return idx // 12, idx % 12 + 1

months = [months_back(TODAY.year, TODAY.month, n) for n in range(5, -1, -1)]


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "NEPSE-Pulse/6.0"})
    with urllib.request.urlopen(req, timeout=90) as response:
        return response.read()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {
        "version": 1,
        "market": "NEPSE",
        "source": BASE,
        "generatedAt": date.today().isoformat(),
        "months": [],
    }
    failures = []
    for year, month in months:
        key = f"{year:04d}-{month:02d}"
        url = f"{BASE}/{key}.json"
        target = OUT / f"{key}.json"
        try:
            payload = json.loads(fetch(url).decode("utf-8"))
            if not isinstance(payload, dict) or not isinstance(payload.get("series"), dict):
                raise ValueError("monthly shard has no series object")
            payload["importedFrom"] = url
            payload["importedAt"] = date.today().isoformat()
            target.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
            manifest["months"].append({
                "month": key,
                "file": f"history/ltp/{key}.json",
                "dates": len(payload.get("dates", [])),
                "symbols": len(payload.get("series", {})),
            })
            print(f"OK {key}: {len(payload.get('series', {}))} symbols / {len(payload.get('dates', []))} dates")
        except Exception as exc:
            failures.append({"month": key, "url": url, "error": str(exc)})
            print(f"WARN {key}: {exc}")

    manifest["failures"] = failures
    manifest["complete"] = len(failures) == 0 and len(manifest["months"]) == 6
    (ROOT / "data" / "history" / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if failures:
        raise SystemExit(f"Six-month history backfill incomplete: {len(failures)} month(s) failed")


if __name__ == "__main__":
    main()
