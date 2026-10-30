#!/usr/bin/env python3
"""Refresh, normalize and validate the static NEPSE market snapshot."""
from __future__ import annotations

import json
import pathlib
import urllib.request
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
BASE = "https://raw.githubusercontent.com/Shubhamnpk/yonepse/main/data/"
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
    securities = fetch("other/securities.json")
    quotes = fetch("market/live.json")
    indices = fetch("market/indices.json")
    summary = fetch("market/summary.json")
    status = fetch("market/status.json")
    ltp_manifest = fetch("ltp/manifest.json")
    mapping = sector_map(fetch("other/sector_codes.json"))
    if not isinstance(securities, list) or not securities:
        raise RuntimeError("Active securities master unavailable; refusing partial coverage")
    if not isinstance(quotes, list) or not quotes:
        raise RuntimeError("Quote snapshot unavailable")

    # Full coverage comes from the active EQUITY master, not today's traded list.
    master = {}
    for item in securities:
        if not isinstance(item, dict):
            continue
        symbol = str(item.get("symbol") or "").strip().upper()
        if symbol and str(item.get("status") or "").upper() == "A" and str(item.get("instrumentType") or "").lower() == "equity":
            if symbol in master:
                raise RuntimeError(f"Duplicate active equity: {symbol}")
            master[symbol] = item
    if len(master) < 200:
        raise RuntimeError(f"Active equity master too small: {len(master)}")

    quote_by_symbol = {}
    for raw in quotes:
        if not isinstance(raw, dict):
            continue
        q = normalize_stock(raw, mapping)
        if not q["symbol"]:
            continue
        if q["symbol"] in quote_by_symbol:
            raise RuntimeError(f"Duplicate quote symbol: {q['symbol']}")
        quote_by_symbol[q["symbol"]] = q
    quote_times = [parse_timestamp(q.get("lastUpdated")) for q in quote_by_symbol.values() if q.get("lastUpdated")]
    quote_times = [t for t in quote_times if t is not None]
    if not quote_times:
        raise RuntimeError("No valid source quote timestamps")
    source_updated_at = max(quote_times).isoformat()

    rows, invalid = [], []
    for symbol, security in sorted(master.items()):
        q = quote_by_symbol.get(symbol)
        sector = security.get("sectorName") or mapping.get(symbol)
        row = canonical_stock(q, sector or "Not supplied") if q else canonical_stock({"symbol": symbol}, sector or "Not supplied")
        row.update({
            "symbol": symbol,
            "name": security.get("companyName") or security.get("securityName") or row.get("name"),
            "sector": sector,
            "securityId": security.get("id"),
            "instrumentType": security.get("instrumentType"),
            "listingStatus": security.get("status"),
            "isTraded": q is not None,
            "quoteStatus": "available" if q else "not_traded_or_quote_unavailable",
            "quoteSource": "YONEPSE public dataset" if q else None
        })
        if q:
            errors = validate_stock(q)
            if errors:
                invalid.append({"symbol": symbol, "errors": errors})
                for field in ("ltp","previousClose","change","changePercent","open","high","low","volume","turnover","trades","marketCap","lastUpdated"):
                    row[field] = None
                row["isTraded"] = False
                row["quoteStatus"] = "quarantined_invalid_quote"
        rows.append(row)

    valid_quotes = sum(x["quoteStatus"] == "available" for x in rows)
    if len(quote_by_symbol) < 200 or valid_quotes < 200:
        raise RuntimeError(f"Quote snapshot failed minimum quality gate: raw={len(quote_by_symbol)}, valid={valid_quotes}")
    now = datetime.now(timezone.utc).isoformat()
    nepse = next((x for x in indices if isinstance(x, dict) and x.get("index") in ("NEPSE", "NEPSE Index")), None)
    missing = sum(x["quoteStatus"] == "not_traded_or_quote_unavailable" for x in rows)
    live = {
        "schemaVersion": 2, "updatedAt": now,
        "source": "YONEPSE public dataset; not independently exchange-verified",
        "sourceUpdatedAt": source_updated_at,
        "upstreamDocumentedCadence": "hourly during market hours",
        "pollingCadence": "GitHub Actions attempts every 5 minutes; upstream cadence is the limiting factor",
        "market": status, "index": nepse, "summary": summary,
        "coverage": {
            "masterSource": "YONEPSE data/other/securities.json",
            "quoteSource": "YONEPSE data/market/live.json",
            "activeEquities": len(master), "quoteRows": len(quote_by_symbol),
            "quotesAvailable": valid_quotes, "noQuoteOrNotTraded": missing,
            "quarantinedQuotes": len(invalid),
            "coverageMeaning": "All active listed equities remain visible. Missing quote fields are null, never fabricated."
        },
        "stocks": rows
    }
    write_json(DATA / "live.json", live)
    write_json(DATA / "sectors.json", {"schemaVersion": 1, "updatedAt": now, "source": "YONEPSE", "sectors": mapping})
    write_json(DATA / "market-summary.json", {"schemaVersion": 1, "updatedAt": now, "source": "YONEPSE", "summary": summary})
    write_json(DATA / "data-quality-report.json", {
        "generatedAt": now, "sourceUpdatedAt": source_updated_at,
        "activeEquities": len(master), "quoteRows": len(quote_by_symbol),
        "quotesAvailable": valid_quotes, "missingOrUntraded": missing,
        "invalidQuoteRows": invalid,
        "quoteSymbolsOutsideActiveEquityMaster": sorted(set(quote_by_symbol) - set(master))
    })

    months = ltp_manifest.get("availableMonths", []) if isinstance(ltp_manifest, dict) else []
    months = [str(m) for m in months if isinstance(m, str)]
    recent_months = months[-4:]
    history_by_symbol: dict[str, list[dict]] = {}
    for month in recent_months:
        shard = fetch(f"ltp/monthly/{month}.json")
        dates, series = shard.get("dates", []), shard.get("series", {})
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
                    di, close, volume = int(point[0]), number(point[1]), number(point[2])
                    if 0 <= di < len(dates) and close is not None and close > 0:
                        bucket.append({"date": dates[di], "close": close, "volume": volume})
                except (TypeError, ValueError):
                    continue
    history_dir = DATA / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    for symbol, items in history_by_symbol.items():
        deduped = {x["date"]: x for x in items}
        ordered = [deduped[k] for k in sorted(deduped)]
        if ordered:
            write_json(history_dir / f"{symbol}.json", ordered)

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
            point = {"date": str(stamp)[:10], "timestamp": stamp, "value": close,
                     "change": number(nepse.get("change")), "percent": number(nepse.get("perChange")),
                     "high": number(nepse.get("high")), "low": number(nepse.get("low"))}
            if not points or points[-1].get("timestamp") != point["timestamp"]:
                points.append(point)
    history["updatedAt"], history["points"] = now, points[-5000:]
    write_json(history_path, history)
    print(f"Active equities={len(master)}; quotes={valid_quotes}; missing={missing}; source={source_updated_at}")


if __name__ == "__main__":
    main()
