# NEPSE Terminal

A lightweight GitHub Pages-compatible market research dashboard.

## Dashboard
The root page is index.html. The archived project remains preserved in /old.

## Current data limitation
The dashboard reads old/data/live.json as an archived snapshot and checks its timestamp. Data older than 15 minutes is marked stale and trade calls are locked. A browser refresh does not update the source feed. The archived snapshot currently has an August 2026 timestamp, so it must not be used for current trading.

## Features
- Market breadth and stock universe overview
- Searchable, sortable stock screener with pagination
- Explicit stale-data warning and signal lockout
- Position sizing calculator based on fixed account risk
- Responsive dark terminal interface with no framework or paid API

## Preview
Run python -m http.server 8000 in the repository folder and open http://localhost:8000.

## Next requirement
Restore a verified market-data workflow that writes fresh root-level data and daily historical candles before using this as an active trading tool.

This is an educational screening interface, not investment advice. Scores are not probabilities of profit. Verify quotes, liquidity, fees and corporate actions before trading.