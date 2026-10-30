#!/usr/bin/env python3
"""Compare YONEPSE snapshot quotes with licensed ShareHub quotes.

This script never promotes a provider or enables trading signals. It writes only
aggregate comparison results; credentials and raw provider payloads are not saved.
"""
from __future__ import annotations

import json
import os
import pathlib
import urllib.request
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
BASE = "https://sharehubnepal.com"


def request_json(url: str, *, method: str = "GET", payload=None, token=None):
    body = json.dumps(payload).encode() if payload is not None else None
    headers = {"Accept": "application/json", "User-Agent": "NEPSE-Terminal-Provider-Check/1.0"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def timestamp(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def main():
    email, password = os.getenv("SHAREHUB_EMAIL"), os.getenv("SHAREHUB_PASSWORD")
    if not email or not password:
        raise SystemExit("Set SHAREHUB_EMAIL and SHAREHUB_PASSWORD as repository Actions secrets.")
    auth = request_json(
        BASE + "/account/api/v1/auth/login/email",
        method="POST",
        payload={"email": email, "password": password, "useOnCookies": False},
    )
    token = ((auth.get("data") or {}).get("accessToken"))
    if not auth.get("success") or not token:
        raise RuntimeError("ShareHub authentication failed; no credentials or response body will be printed.")

    response = request_json(BASE + "/data/api/v1/nepse-data/stock-prices", token=token)
    if not response.get("success") or not isinstance(response.get("data"), list):
        raise RuntimeError("ShareHub stock-prices response was unsuccessful or had an unexpected schema.")
    provider_rows = response["data"]
    provider = {}
    for row in provider_rows:
        if not isinstance(row, dict):
            continue
        symbol = str(row.get("symbol") or "").strip().upper()
        if not symbol:
            continue
        if symbol in provider:
            raise RuntimeError("Duplicate symbol in ShareHub response: " + symbol)
        provider[symbol] = row

    local_path = DATA / "live.json"
    local = json.loads(local_path.read_text(encoding="utf-8"))
    local_rows = {str(x.get("symbol") or "").upper(): x for x in local.get("stocks", []) if isinstance(x, dict) and x.get("symbol")}
    common = sorted(set(provider) & set(local_rows))
    compared, missing_ltp, discrepancies = 0, 0, []
    for symbol in common:
        a = provider[symbol].get("ltp")
        b = local_rows[symbol].get("ltp")
        try:
            a, b = float(a), float(b)
        except (TypeError, ValueError):
            missing_ltp += 1
            continue
        if a <= 0 or b <= 0:
            missing_ltp += 1
            continue
        compared += 1
        diff = abs(a - b) / max(abs(a), abs(b)) * 100
        if diff > 0.5:
            discrepancies.append({"symbol": symbol, "sharehubLtp": a, "yonepseLtp": b, "differencePercent": round(diff, 4)})

    quote_times = [timestamp(row.get("lastUpdatedTime")) for row in provider.values()]
    quote_times = [x for x in quote_times if x]
    latest = max(quote_times).isoformat() if quote_times else None
    age_minutes = (datetime.now(timezone.utc) - max(quote_times)).total_seconds() / 60 if quote_times else None
    matched_ratio = compared / max(1, len(local_rows))
    mismatch_ratio = len(discrepancies) / max(1, compared)
    preliminary = (
        len(provider) >= 200 and compared >= 200 and matched_ratio >= 0.90
        and mismatch_ratio <= 0.02 and age_minutes is not None and -5 <= age_minutes <= 15
    )
    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "provider": "ShareHub licensed NEPSE Data API",
        "providerDocumentedCadence": "~20 seconds during trading hours; ~5 minutes when market closed",
        "comparison": "ShareHub LTP against YONEPSE LTP; same-session timestamps are not guaranteed identical",
        "providerQuoteCount": len(provider),
        "yonepseActiveEquityCount": len(local_rows),
        "matchedSymbols": len(common),
        "validLtpPairsCompared": compared,
        "missingOrInvalidLtpPairs": missing_ltp,
        "matchedCoverageRatio": round(matched_ratio, 4),
        "latestShareHubQuoteTimestamp": latest,
        "shareHubQuoteAgeMinutes": round(age_minutes, 2) if age_minutes is not None else None,
        "ltpDiscrepanciesOver0_5Percent": len(discrepancies),
        "discrepancyRatio": round(mismatch_ratio, 4),
        "largestDiscrepancies": sorted(discrepancies, key=lambda x: x["differencePercent"], reverse=True)[:30],
        "preliminaryTechnicalGate": "candidate_pass" if preliminary else "not_passed",
        "humanReviewRequired": True,
        "tradeSignalsEnabled": False,
        "note": "A candidate pass is not independent proof of exchange accuracy. Review multiple same-session samples and source terms before any manual promotion."
    }
    (DATA / "provider-comparison.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("providerQuoteCount","yonepseActiveEquityCount","validLtpPairsCompared","matchedCoverageRatio","shareHubQuoteAgeMinutes","ltpDiscrepanciesOver0_5Percent","preliminaryTechnicalGate","tradeSignalsEnabled")}, indent=2))


if __name__ == "__main__":
    main()
