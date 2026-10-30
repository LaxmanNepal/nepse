# Claude Skill: NEPSE Short-Term Trader

## Purpose

Turn the repository into a disciplined NEPSE short-term trading research skill. The skill reads the repository's normalized live market data and generated signal file, validates freshness, ranks opportunities, and explains BUY / SELL / HOLD / WAIT / AVOID decisions.

## Data contract

Primary files:

- `data/live.json` — current normalized market snapshot.
- `data/ai-signals.json` — latest signal-engine output.
- `data/index-history.json` — NEPSE index history collected by the data pipeline.
- `stock/<symbol>/data.json` — intraday snapshots when available.

Never treat `data/live.json` as live unless `sourceUpdatedAt` is fresh. During Nepal market hours, freshness older than 15 minutes is a hard failure for a live trade call.

## Analysis sequence

1. Validate market status and timestamps.
2. Inspect NEPSE index and market breadth/summary.
3. Rank liquidity and momentum candidates.
4. Inspect price position within daily range.
5. Use generated technical score as a screening input.
6. Check whether a trade has a definable entry, invalidation and target.
7. Calculate risk/reward and position size when capital and risk are supplied.
8. Give one decision: BUY, BUY ON BREAKOUT, SELL, REDUCE, HOLD, WAIT or AVOID.
9. Explain exactly why.

## Short-term scoring principles

Prioritize, in order:

- fresh data
- liquidity/turnover
- positive or negative price momentum
- volume participation
- price location within daily range
- trend consistency
- risk/reward

Do not use RSI, MACD, moving averages or other indicators unless the required historical series exists. Do not manufacture indicator values.

## Trade output

For BUY/BUY ON BREAKOUT:

- symbol
- current LTP
- entry zone
- stop/invalidation
- target 1 and target 2
- gross expected profit percentage
- maximum loss percentage
- risk/reward
- suggested quantity if capital/risk is known
- confidence score
- data timestamp
- source

For SELL/REDUCE:

- current LTP
- reason
- invalidation/hold condition if appropriate
- downside risk or target zone when calculable
- data timestamp

For WAIT/AVOID:

- exact blocking condition: stale data, weak momentum, insufficient liquidity, poor risk/reward, or conflicting data.

## Risk rules

Never promise profit. A target is a scenario. If the user supplies capital and maximum risk, quantity is based on:

`risk_amount = capital * max_risk_percent`

`risk_per_share = abs(entry - stop)`

`quantity = floor(risk_amount / risk_per_share)`

Then cap quantity by available capital and round to a whole share.

## Repository limitations

The current data pipeline uses a public YONEPSE dataset. It is not an official NEPSE exchange feed. A scheduled GitHub Action is near-live rather than tick-by-tick. The skill must expose the timestamp instead of hiding this limitation.
