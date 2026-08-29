# NEPSE Pulse

A static-first Nepal stock market research platform.

## Architecture

- **Frontend:** HTML, CSS and vanilla JavaScript.
- **Canonical live dataset:** `data/live.json`.
- **Generated company datasets:** `stock/<symbol>/data.json`.
- **Automation:** GitHub Actions collects and validates market/news data.
- **Optional backend:** Express service in `nepse-backend/`.

## Development

```bash
python scripts/validate_market_data.py
python scripts/validate_site.py
```

Optional backend:

```bash
npm install
npm start
```

## UI rule

The project uses one shared header entry point: `shared-header.js` and one consolidated application layer: `app.css`. New page work should not add another competing global theme or navbar.

## Data rule

`data/live.json` is the primary local market payload. External sources are fallback only. All new code should normalize data from that model rather than inventing additional schemas.

## Disclaimer

Market information is informational and should not be treated as personalized investment advice.
