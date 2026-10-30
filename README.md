# NEPSE Terminal

A lightweight, GitHub Pages-compatible NEPSE market research dashboard and conservative technical screening engine.

## Dashboard

The root page is `index.html`. The previous implementation is preserved under `/old`.

## Data pipeline

- Reads the YONEPSE public static dataset.
- Normalizes the daily stock snapshot and validates source rows.
- Quarantines isolated malformed stock rows; rejects a feed when too many rows fail quality checks.
- Imports the latest four monthly LTP shards into `data/history/{SYMBOL}.json`.
- Calculates indicators only when sufficient daily history exists.
- Writes `data/live.json` and `data/ai-signals.json`.
- GitHub Actions refreshes on a five-minute schedule during the approximate NEPSE session and on manual/push triggers.

Source dataset: https://github.com/Shubhamnpk/yonepse  
Source API docs: https://shubhamnpk.github.io/yonepse/pages/docs.html

## Dashboard features

- NEPSE index and market breadth
- Searchable, sortable stock screener with pagination
- BUY confirmation / WATCH / WAIT / AVOID / SELL-review screening
- Indicator and history-aware scoring
- Position sizing calculator based on fixed account risk
- Stale-feed lockout and source timestamp display
- Responsive dark terminal interface; no frontend framework or paid API

## Data and trading limitations

This is a research screener, not an execution system or investment adviser. YONEPSE is a third-party public dataset and may be delayed, incomplete, or unavailable. GitHub Actions schedules are not tick-by-tick streaming and may be delayed. A quote snapshot is not a live order-book feed.

Signals are heuristic screens, not probabilities of profit. BUY ON CONFIRMATION requires adequate daily history and technical conditions; even then, verify the quote, volume, spread, market depth, corporate actions, circuit limits, and broker charges before placing an order. SELL / REDUCE is a review prompt for an existing holding, not a short-selling instruction. Never rely on stale data.

The dashboard locks active signals when the latest quote timestamp is older than 15 minutes. After market close, the data may be stale for intraday execution even though it remains useful for historical review.

## Run locally

From the repository root:

```bash
python -m http.server 8000
```

Open http://localhost:8000.

## GitHub Pages

The Pages workflow deploys from GitHub Actions. In repository Settings → Pages, the build and deployment source must be set to **GitHub Actions**.

## License and attribution

This project is independent and uses the public YONEPSE dataset. Review the upstream repository's license and attribution requirements before redistributing data.
