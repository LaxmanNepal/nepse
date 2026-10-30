# NEPSE Terminal

A lightweight, GitHub Pages-compatible NEPSE market research dashboard and conservative technical screening engine.

## Dashboard

The root page is `index.html`. The previous implementation is preserved under `/old`.

## Data pipeline

- Uses YONEPSE's active-equity securities master as the coverage universe, not only the daily traded-stock snapshot.
- Keeps every active listed equity visible; unavailable quotes remain null and are never converted to zero.
- Quarantines invalid quote fields without deleting the listed security; writes data/data-quality-report.json with coverage and validation counts.
- Preserves source quote timestamps separately from pipeline generation time.
- Imports the latest four monthly LTP shards into `data/history/{SYMBOL}.json`.
- Calculates indicators only when sufficient daily history exists.
- Writes `data/live.json` and `data/ai-signals.json`.
- GitHub Actions attempts polling every five minutes during the configured session. YONEPSE documentation describes hourly upstream updates, so polling more often does not make the source five-minute or real-time.
- Every snapshot is marked `sourceVerification.status=unverified` and `tradeSignalsEnabled=false` until an independent licensed-provider comparison is completed.
- The signal generator fails closed: it emits an empty `LOCKED_UNVERIFIED_SOURCE` file rather than BUY/SELL/WATCH calls from an unverified snapshot.
- ShareHub is the candidate licensed intraday provider. Its documented API claims ~20-second market-hour refresh, but requires a licence, bearer authentication and server-IP allowlisting. A static-egress/self-hosted runner is required for reliable allowlisting; GitHub-hosted runner IPs are not suitable for a fixed allowlist.
- Do not set source verification to `verified` or enable trade signals until same-session prices and timestamps have been independently compared and a documented tolerance has passed.

Source dataset: https://github.com/Shubhamnpk/yonepse
Source cadence and attribution: https://shubhamnpk.github.io/yonepse/pages/docs.html and https://shubhamnpk.github.io/yonepse/pages/sources.html
Candidate licensed intraday provider: ShareHub documents an all-stock price API with ~20-second refresh during trading; requires a licence and server-IP allowlisting: https://sharehubnepal.com/data/nepse-data-documentation/  
Source API docs: https://shubhamnpk.github.io/yonepse/pages/docs.html

## Dashboard features

- NEPSE index and market breadth
- Searchable, sortable stock screener with pagination, including active listed equities without a current quote
- BUY confirmation / WATCH / WAIT / AVOID / SELL-review screening
- Indicator and history-aware scoring
- Position sizing calculator based on fixed account risk
- Stale-feed lockout, source timestamp display, full active-equity coverage and explicit missing-quote status
- Responsive dark terminal interface; no frontend framework or paid API

## Data and trading limitations

This is a research screener, not an execution system or investment adviser. YONEPSE is a third-party public dataset and may be delayed, incomplete, or unavailable. GitHub Actions schedules are not tick-by-tick streaming and may be delayed. A quote snapshot is not a live order-book feed.

Signals are heuristic screens, not probabilities of profit. BUY ON CONFIRMATION requires adequate daily history and technical conditions; even then, verify the quote, volume, spread, market depth, corporate actions, circuit limits, and broker charges before placing an order. SELL / REDUCE is a review prompt for an existing holding, not a short-selling instruction. Never rely on stale data.

The dashboard locks active signals unless the source is independently verified AND the latest quote timestamp is under 15 minutes old. After market close, the data may be stale for intraday execution even though it remains useful for historical review.

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
