# NEPSE data and signal scripts

## Update sequence

1. `update_live_market.py` downloads the canonical YONEPSE `market/live.json` quote snapshot, index/summary/status, sector map, and the latest four `ltp/monthly/YYYY-MM.json` shards.
2. It normalizes and validates stock rows, quarantines isolated invalid rows, and rejects a source snapshot when the rejected share exceeds the configured threshold.
3. It writes `data/live.json`, market metadata, index history, and per-symbol daily histories under `data/history/{SYMBOL}.json`.
4. `generate_ai_signals.py` calculates RSI, SMA/EMA, MACD, and relative volume only where enough history exists, then writes `data/ai-signals.json`.

## Upstream source

- Repository: https://github.com/Shubhamnpk/yonepse
- Canonical quote endpoint: `data/market/live.json`
- Index endpoint: `data/market/indices.json`
- Monthly price history: `data/ltp/manifest.json` and `data/ltp/monthly/YYYY-MM.json`
- API documentation: https://shubhamnpk.github.io/yonepse/pages/docs.html

Monthly LTP shards are sparse daily close/volume/turnover/trade observations, not intraday candles or order-book depth. The engine must not represent them as intraday history.

## Run locally

```bash
python -m compileall -q scripts
python scripts/update_live_market.py
python scripts/generate_ai_signals.py
```

No signal is a guarantee or a probability of profit. Verify freshness, liquidity, broker costs, circuit limits, corporate actions and the live quote independently.
