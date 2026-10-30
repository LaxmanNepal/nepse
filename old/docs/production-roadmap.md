# Production NEPSE Roadmap

## Architecture

`NEPSE sources -> collector -> validation/cache -> database -> REST API -> web UI`

## Intraday collection

Store UTC timestamps. During Monday-Friday 11:00-15:00 Asia/Kathmandu, execute a one-minute collector, validate the response, deduplicate `(symbol,timestamp)`, and persist the snapshot. Outside the window, the UI must label the data as latest available.

## API

- `/api/v1/market/summary`
- `/api/v1/stocks?search=`
- `/api/v1/stocks/:symbol`
- `/api/v1/stocks/:symbol/intraday?interval=1m`
- `/api/v1/stocks/:symbol/history?interval=1d`
- `/api/v1/stocks/:symbol/fundamentals`
- `/api/v1/stocks/:symbol/financials`
- `/api/v1/stocks/:symbol/actions`
- `/api/v1/stocks/:symbol/announcements`
- `/api/v1/sectors`
- `/api/v1/market/gainers`
- `/api/v1/market/losers`
- `/api/v1/market/turnover`

## Frontend modules already added

- `api.js`: cached, normalized data access and Nepal market-time helpers.
- `technical.js`: SMA, EMA, RSI, MACD, Bollinger Bands and a mechanical trend score.

The static YONEPSE dataset remains the fallback until the production collector/API is deployed.
