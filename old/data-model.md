# NEPSE Pulse Data Model

## Canonical collections

- `market_snapshots`: one validated market snapshot per source timestamp.
- `intraday_quotes`: symbol, timestamp_utc, ltp, open, high, low, close, volume, turnover, trades.
- `companies`: symbol, company name, sector, address, website, contacts.
- `financials`: symbol, fiscal year/quarter, revenue, profit, EPS, book value, assets, liabilities, equity, ROE and related ratios.
- `corporate_actions`: symbol, action type, announced date, book closure, record date, ratio/rate.
- `announcements`: symbol, title, published timestamp, source URL.
- `index_history`: index symbol, business date, close/value, high, low, change and percent change.

## Time rules

Store timestamps in UTC. Convert only at the presentation boundary to `Asia/Kathmandu`.

NEPSE trading days are **Sunday–Thursday**, normally **11:00–15:00 Nepal time**. Friday and Saturday are non-trading days. Collectors must use the exchange's actual market status rather than assuming a weekday schedule when the source provides one.

Outside the trading window the UI must label data as the latest available record, not live.

## Frontend data rules

`data/live.json` is the primary local live market payload.

`data/history/ltp/YYYY-MM.json` is the six-month LTP/volume/turnover/trades archive.

`data/index-history.json` is reserved for verified daily index history. The UI must never manufacture historical index points from unrelated stock or market-summary data.

Technical indicators that require OHLC data must be calculated only from genuine daily OHLC/close history. LTP-only history may be displayed as LTP history but must not be labelled OHLC technical history.

## API contract

`GET /api/v1/market/summary`

`GET /api/v1/stocks?search=NABIL`

`GET /api/v1/stocks/:symbol`

`GET /api/v1/stocks/:symbol/intraday?interval=1m&from=&to=`

`GET /api/v1/stocks/:symbol/history?interval=1d&from=&to=`

`GET /api/v1/stocks/:symbol/fundamentals`

`GET /api/v1/stocks/:symbol/financials`

`GET /api/v1/stocks/:symbol/actions`

`GET /api/v1/stocks/:symbol/announcements`

`GET /api/v1/sectors`

`GET /api/v1/market/gainers`

`GET /api/v1/market/losers`

`GET /api/v1/market/turnover`
