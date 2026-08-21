# NEPSE Pulse Data Model

## Required collections/tables

- `market_snapshots`: one validated market snapshot per source timestamp.
- `intraday_quotes`: symbol, timestamp_utc, ltp, open, high, low, close, volume, turnover, trades.
- `companies`: symbol, company name, sector, address, website, contacts.
- `financials`: symbol, fiscal year/quarter, revenue, profit, EPS, book value, assets, liabilities, equity, ROE and related ratios.
- `corporate_actions`: symbol, action type, announced date, book closure, record date, ratio/rate.
- `announcements`: symbol, title, published timestamp, source URL.

## Time rules

Store timestamps in UTC. Convert only at the presentation boundary to `Asia/Kathmandu`. The UI displays Bikram Sambat and Nepali time.

The intended NEPSE collection window is Monday-Friday, 11:00-15:00 Nepal time. A collector should execute once per minute during that window, validate the source response, deduplicate by `(symbol,timestamp)` and persist the snapshot. Outside that window the UI must label the dataset as the latest available record rather than live.

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

The frontend can continue using the static YONEPSE source as a fallback until the collector/API is deployed.
