# NEPSE Pulse API Contract

NEPSE Pulse is static-first. The JSON files under `data/` are the public data contract; the optional Express backend must expose the same normalized concepts rather than creating a second source of truth.

## Canonical snapshot

`data/live.json`

```json
{
  "updatedAt": "ISO-8601 UTC",
  "source": "source identifier",
  "sourceUpdatedAt": "ISO-8601 UTC or null",
  "market": {},
  "index": {},
  "summary": {},
  "stocks": []
}
```

## Stock contract

The canonical stock fields are:

- `symbol`
- `name`
- `sector`
- `ltp`
- `previousClose`
- `change`
- `changePercent`
- `open`
- `high`
- `low`
- `volume`
- `turnover`
- `trades`
- `marketCap`
- `lastUpdated`

Missing values must be `null`, never a fabricated zero.

## Intelligence layer

The Node module `lib/market-engine.js` provides deterministic functions for normalization, market breadth, movers, sector aggregation, screening, and snapshot health. These functions are intentionally independent of HTTP and credentials so the browser, Actions, and optional backend can share the same logic.

## Freshness

Consumers should use `sourceUpdatedAt` when available. Recommended display states are `fresh` (<=5 minutes), `aging` (5–15 minutes), `stale` (>15 minutes), and `unknown` when source freshness is unavailable.

## Financial disclaimer

NEPSE Pulse provides market information and research tooling for informational purposes. Screening and analytical outputs are not personalized investment advice.
