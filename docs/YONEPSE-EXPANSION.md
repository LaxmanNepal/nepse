# NEPSE Pulse: YONEPSE-inspired platform expansion

This document describes an incremental, source-aware expansion of NEPSE Pulse. It is inspired by the feature categories and general architecture of YONEPSE; it is not a claim that every YONEPSE endpoint or scraper has been reproduced.

## Current implementation in this change

- Adds a responsive Market Explorer at `/market/`.
- Reads the repository's existing `data/live.json` snapshot; no third-party live API is required by this page.
- Supports stock search, movement filters, sorting by turnover/change/LTP/volume/symbol, and summary totals derived from available records.
- Adds a platform data validation script and GitHub Actions workflow.
- Preserves the existing root dashboard, canonical live payload, historical LTP shards, company page, shared application styles, and existing automation.

## Data contract and safety

The market explorer tolerates common field aliases, but `data/live.json` remains the canonical source. Do not fabricate live values, historical candles, IPO states, dividends, financial statements, broker details, or notices when a verified source is unavailable. Every new dataset should document its upstream source, collection timestamp, coverage, and known gaps.

## Target feature groups

1. Market: index values, breadth, turnover, volume, trades, movers, sectors, supply/demand.
2. Securities: searchable list, company profile, logo, price history, company financials.
3. Corporate information: announcements, dividends, disclosures, exchange notices.
4. Primary market: IPO/FPO/right-share applications, opening/closing dates, allotment links.
5. Reference data: brokers, TMS links, sector mapping, security types.
6. Historical data: daily LTP/volume/turnover/trades, index series, data manifests.
7. Delivery: static JSON on GitHub Pages plus optional Express endpoints for richer queries.

These groups must be implemented only when source availability and legal/technical access are verified. Public-facing data must display source and freshness information. The site is informational, not personalized investment advice.

## Suggested API resource design

- `GET /api/market/status`
- `GET /api/market/live`
- `GET /api/market/summary`
- `GET /api/market/indices`
- `GET /api/market/sectors`
- `GET /api/stocks`
- `GET /api/stocks/:symbol`
- `GET /api/stocks/:symbol/history`
- `GET /api/company/:symbol`
- `GET /api/ipo/upcoming`
- `GET /api/dividend/history`
- `GET /api/brokers`
- `GET /api/ltp/manifest`
- `GET /api/ltp/:year/:month`
- `GET /api/notifications`

The optional API should normalize existing JSON data rather than create a competing schema. Keep endpoints read-only unless a specific authenticated write use case is designed.

## Local verification

```bash
python scripts/validate_platform_data.py
python scripts/validate_market_data.py
python scripts/validate_site.py
```

The Market Explorer is a static page and works with GitHub Pages when the repository's Pages workflow is enabled.
