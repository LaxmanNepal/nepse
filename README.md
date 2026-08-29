# NEPSE Pulse

A static-first Nepal stock market research platform.

## Architecture

- **Frontend:** HTML, CSS and vanilla JavaScript.
- **Canonical live dataset:** `data/live.json`.
- **Six-month company price history:** `data/history/ltp/YYYY-MM.json`.
- **History manifest:** `data/history/manifest.json`.
- **Generated company datasets:** `stock/<symbol>/data.json`.
- **Automation:** GitHub Actions collects, backfills and validates market data.
- **Optional backend:** Express service in `nepse-backend/`.

## Historical data

The rolling history job downloads the current month plus the five preceding calendar months from the public YONEPSE monthly LTP archive. Each shard contains all available symbols and daily LTP, volume, turnover and transaction counts. The job runs weekly and automatically refreshes the current six-month window.

This is **price/market history**, not a promise of complete corporate fundamentals. Corporate actions, delistings and renamed securities must be handled separately.

## Development

```bash
python scripts/validate_market_data.py
python scripts/validate_site.py
python scripts/backfill_six_months.py
```

Optional backend:

```bash
npm install
npm start
```

## UI rule

The project uses one shared header entry point: `shared-header.js` and one consolidated application layer: `app.css`. New page work should not add another competing global theme or navbar.

## Data rule

`data/live.json` is the primary local market payload. Historical LTP shards are the primary local historical dataset. External sources are used by scheduled import jobs and as controlled fallbacks. New code should normalize data instead of inventing additional schemas.

## Disclaimer

Market information is informational and should not be treated as personalized investment advice.
