#!/usr/bin/env python3
"""Generate transparent short-term screening signals from the normalized live snapshot.

This is a screening engine, not a price-prediction model. It deliberately avoids inventing
longer-term indicators when the required historical series is unavailable.
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIVE = ROOT / "data/live.json"
OUT = ROOT / "data/ai-signals.json"


def num(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def clamp(v, lo=0.0, hi=100.0):
    return max(lo, min(hi, v))


def score_stock(s):
    ltp = num(s.get("ltp"))
    prev = num(s.get("previous_close"))
    high = num(s.get("high"))
    low = num(s.get("low"))
    pct = num(s.get("percent_change"))
    volume = num(s.get("volume"))
    turnover = num(s.get("turnover"))

    if ltp <= 0 or prev <= 0 or high < low or high <= 0:
        return None
    if turnover < 100_000 or volume < 100:
        return None

    rng = high - low
    range_pos = (ltp - low) / rng if rng > 0 else 0.5

    # Transparent 100-point screening model.
    momentum = clamp(50 + pct * 12, 0, 100)       # 0.0% => 50
    range_score = clamp(range_pos * 100)
    liquidity = clamp((math.log10(max(turnover, 1)) - 5) * 18 + 10)
    volume_score = clamp((math.log10(max(volume, 1)) - 2) * 20 + 20)

    score = round(
        0.35 * momentum +
        0.25 * range_score +
        0.25 * liquidity +
        0.15 * volume_score,
        1,
    )

    # Conservative labels. A BUY requires positive momentum and strong range position.
    if score >= 75 and pct >= 0.75 and range_pos >= 0.70:
        action = "BUY"
    elif score >= 68 and pct >= 0.30 and range_pos >= 0.60:
        action = "BUY ON BREAKOUT"
    elif score <= 28 and pct <= -1.0 and range_pos <= 0.35:
        action = "SELL"
    elif score <= 38 and pct < -0.5:
        action = "AVOID"
    else:
        action = "WAIT"

    # Scenario levels use the current day's range. They are explicitly not predictions.
    if action in {"BUY", "BUY ON BREAKOUT"}:
        stop = low if low < ltp else ltp * 0.97
        risk = ltp - stop
        if risk <= 0:
            return None
        target1 = ltp + 1.5 * risk
        target2 = ltp + 2.5 * risk
    elif action == "SELL":
        stop = high if high > ltp else ltp * 1.03
        risk = stop - ltp
        target1 = ltp - 1.5 * risk if risk > 0 else None
        target2 = ltp - 2.5 * risk if risk > 0 else None
    else:
        stop = target1 = target2 = None

    return {
        "symbol": str(s.get("symbol", "")).upper(),
        "name": s.get("name", ""),
        "action": action,
        "score": score,
        "ltp": ltp,
        "percent_change": pct,
        "volume": volume,
        "turnover": turnover,
        "range_position": round(range_pos, 4),
        "high": high,
        "low": low,
        "entry": ltp if action in {"BUY", "SELL"} else None,
        "stop": round(stop, 2) if stop is not None else None,
        "target1": round(target1, 2) if target1 is not None else None,
        "target2": round(target2, 2) if target2 is not None else None,
        "method": "live snapshot screening; no invented historical indicators",
    }


def main():
    live = json.loads(LIVE.read_text(encoding="utf-8"))
    stocks = live.get("stocks", [])
    signals = [x for s in stocks if isinstance(s, dict) for x in [score_stock(s)] if x]

    priority = {"BUY": 0, "BUY ON BREAKOUT": 1, "WAIT": 2, "AVOID": 3, "SELL": 4}
    signals.sort(key=lambda x: (priority.get(x["action"], 9), -x["score"], -x["turnover"]))

    buys = [x for x in signals if x["action"] in {"BUY", "BUY ON BREAKOUT"}][:10]
    sells = [x for x in signals if x["action"] == "SELL"][:10]
    avoids = [x for x in signals if x["action"] == "AVOID"][:10]

    output = {
        "schemaVersion": 1,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "sourceUpdatedAt": live.get("sourceUpdatedAt"),
        "source": live.get("source"),
        "engine": "NEPSE Pulse transparent short-term screener v1",
        "warning": "Screening scenarios are not guaranteed returns or personalized investment advice.",
        "counts": {"stocks_scored": len(signals)},
        "topBuy": buys,
        "topSell": sells,
        "topAvoid": avoids,
    }
    OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {len(buys)} buy candidates, {len(sells)} sell candidates, {len(avoids)} avoid candidates from {len(signals)} liquid stocks")


if __name__ == "__main__":
    main()
