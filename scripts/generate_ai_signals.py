#!/usr/bin/env python3
"""Generate conservative NEPSE short-term signals with historical technical indicators.

The engine only calculates RSI, MACD, SMA/EMA and relative volume when a valid daily
price history file exists. The current public snapshot alone is not historical data.
No probability of profit is claimed; scores are heuristic screening scores.
"""
from __future__ import annotations

import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIVE_PATH = ROOT / "data/live.json"
OUT_PATH = ROOT / "data/ai-signals.json"
HISTORY_DIR = ROOT / "data/history"
STOCK_DIR = ROOT / "stock"


def number(value):
    try:
        x = float(value)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None


def mean(values):
    return sum(values) / len(values) if values else None


def sma(values, period):
    return mean(values[-period:]) if len(values) >= period else None


def ema_series(values, period):
    if len(values) < period:
        return []
    k = 2 / (period + 1)
    result = [mean(values[:period])]
    for value in values[period:]:
        result.append(value * k + result[-1] * (1 - k))
    return result


def rsi(values, period=14):
    if len(values) < period + 1:
        return None
    changes = [values[i] - values[i - 1] for i in range(1, len(values))]
    recent = changes[-period:]
    gains = [max(x, 0) for x in recent]
    losses = [max(-x, 0) for x in recent]
    avg_gain, avg_loss = mean(gains), mean(losses)
    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def macd(values):
    fast, slow = ema_series(values, 12), ema_series(values, 26)
    if not fast or not slow:
        return None
    # Align EMA series to the latest 26-period EMA dates.
    offset = 26 - 12
    macd_line = [fast[i + offset] - slow[i] for i in range(len(slow))]
    signal = ema_series(macd_line, 9)
    if not signal:
        return {"line": round(macd_line[-1], 4), "signal": None, "histogram": None}
    line_aligned = macd_line[-len(signal):]
    return {
        "line": round(line_aligned[-1], 4),
        "signal": round(signal[-1], 4),
        "histogram": round(line_aligned[-1] - signal[-1], 4),
    }


def load_history(symbol):
    candidates = [
        HISTORY_DIR / f"{symbol}.csv",
        HISTORY_DIR / f"{symbol}.json",
        STOCK_DIR / symbol.lower() / "history.json",
        STOCK_DIR / symbol.lower() / "data.json",
    ]
    for path in candidates:
        if not path.exists():
            continue
        try:
            if path.suffix == ".csv":
                with path.open(newline="", encoding="utf-8-sig") as f:
                    rows = list(csv.DictReader(f))
            else:
                raw = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    raw = raw.get("history") or raw.get("prices") or raw.get("data") or []
                rows = raw if isinstance(raw, list) else []
            closes, volumes, dates = [], [], []
            for row in rows:
                if not isinstance(row, dict):
                    continue
                close = number(row.get("close") or row.get("ltp") or row.get("price") or row.get("LTP"))
                volume = number(row.get("volume") or row.get("quantity") or row.get("totalTradedQuantity"))
                date = row.get("date") or row.get("timestamp") or row.get("businessDate")
                if close and close > 0:
                    closes.append(close)
                    volumes.append(volume or 0)
                    dates.append(date)
            if closes:
                return closes, volumes, dates, str(path.relative_to(ROOT))
        except (OSError, json.JSONDecodeError, csv.Error):
            continue
    return [], [], [], None


def score_stock(stock):
    ltp = number(stock.get("ltp"))
    previous = number(stock.get("previous_close", stock.get("previousClose")))
    high, low = number(stock.get("high")), number(stock.get("low"))
    pct = number(stock.get("percent_change", stock.get("changePercent")))
    volume, turnover = number(stock.get("volume")), number(stock.get("turnover"))
    if not ltp or ltp <= 0 or not previous or previous <= 0 or high is None or low is None or high < low:
        return None
    if (turnover or 0) < 100_000 or (volume or 0) < 100:
        return None

    closes, hist_volumes, dates, history_source = load_history(str(stock.get("symbol", "")).upper())
    # Avoid counting today's LTP twice if the historical series already ends at today's close.
    if closes and abs(closes[-1] - ltp) / ltp > 0.15:
        # Likely a mismatched or adjusted series; do not use its indicators.
        closes, hist_volumes, dates, history_source = [], [], [], None
    if not closes or abs(closes[-1] - ltp) / ltp > 0.03:
        closes = closes + [ltp]
        hist_volumes = hist_volumes + [volume or 0]
        dates = dates + [stock.get("last_updated") or stock.get("lastUpdated")]

    rng = high - low
    range_position = (ltp - low) / rng if rng > 0 else 0.5
    momentum_score = max(0, min(100, 50 + (pct or 0) * 10))
    range_score = max(0, min(100, range_position * 100))
    liquidity_score = max(0, min(100, (math.log10(max(turnover or 1, 1)) - 5) * 18 + 10))
    volume_score = max(0, min(100, (math.log10(max(volume or 1, 1)) - 2) * 20 + 20))

    sma20, sma50 = sma(closes, 20), sma(closes, 50)
    ema12, ema26 = ema_series(closes, 12), ema_series(closes, 26)
    rsi14 = rsi(closes, 14)
    macd_value = macd(closes)
    avg_volume20 = mean(hist_volumes[-21:-1]) if len(hist_volumes) >= 21 else None
    relative_volume = (volume / avg_volume20) if avg_volume20 and avg_volume20 > 0 else None

    technical_score = None
    trend_score = None
    if sma20 is not None:
        trend_score = 100 if ltp > sma20 else 35
        if sma50 is not None:
            trend_score = (trend_score + (100 if sma20 > sma50 else 35)) / 2
    if rsi14 is not None and macd_value and macd_value.get("histogram") is not None and trend_score is not None:
        rsi_score = 75 if 50 <= rsi14 <= 68 else 45 if rsi14 > 75 or rsi14 < 35 else 60
        macd_score = 75 if macd_value["histogram"] > 0 else 35
        technical_score = 0.4 * trend_score + 0.3 * rsi_score + 0.3 * macd_score

    base_score = 0.35 * momentum_score + 0.25 * range_score + 0.25 * liquidity_score + 0.15 * volume_score
    score = round(0.65 * base_score + 0.35 * technical_score, 1) if technical_score is not None else round(base_score, 1)
    history_ok = len(closes) >= 50 and technical_score is not None
    if not history_ok:
        # Current-day snapshot is not enough to justify an outright BUY.
        if score >= 68 and (pct or 0) >= 0.3 and range_position >= 0.6:
            action = "WATCH BREAKOUT"
        elif score <= 38 and (pct or 0) < -0.5:
            action = "AVOID"
        else:
            action = "WAIT"
    elif score >= 78 and (pct or 0) > 0 and 48 <= (rsi14 or 0) <= 70 and macd_value["histogram"] > 0 and ltp > sma20 and (relative_volume is None or relative_volume >= 1.2) and range_position >= 0.65:
        action = "BUY ON CONFIRMATION"
    elif score <= 30 and (pct or 0) < -1.0 and range_position <= 0.35 and macd_value["histogram"] < 0:
        action = "SELL / REDUCE (REVIEW HOLDING)"
    elif score <= 40 and (pct or 0) < -0.5:
        action = "AVOID"
    else:
        action = "WAIT"

    # Stop/targets only when a technically defensible entry/stop can be defined.
    entry = stop = target1 = target2 = risk_reward = None
    if action == "BUY ON CONFIRMATION":
        entry = round(ltp, 2)
        support = sma20 if sma20 and sma20 < ltp else low
        stop = round(min(support, ltp * 0.97), 2)
        risk = entry - stop
        if risk > 0:
            target1, target2 = round(entry + 1.5 * risk, 2), round(entry + 2.5 * risk, 2)
            risk_reward = "1:1.5 / 1:2.5"
        else:
            action, entry, stop = "WAIT", None, None
    elif action.startswith("SELL"):
        entry = round(ltp, 2)
        stop = round(high if high > ltp else ltp * 1.03, 2)
        risk = stop - entry
        if risk > 0:
            target1, target2 = round(max(0, entry - 1.5 * risk), 2), round(max(0, entry - 2.5 * risk), 2)
            risk_reward = "downside scenario 1.5R / 2.5R"

    return {
        "symbol": str(stock.get("symbol", "")).upper(),
        "name": stock.get("name", ""),
        "sector": stock.get("sector", "Unknown"),
        "action": action,
        "score": score,
        "ltp": ltp,
        "percent_change": pct,
        "volume": volume,
        "turnover": turnover,
        "high": high,
        "low": low,
        "range_position": round(range_position, 4),
        "indicators": {
            "history_points": len(closes),
            "history_source": history_source,
            "rsi14": round(rsi14, 2) if rsi14 is not None else None,
            "sma20": round(sma20, 2) if sma20 is not None else None,
            "sma50": round(sma50, 2) if sma50 is not None else None,
            "ema12": round(ema12[-1], 2) if ema12 else None,
            "ema26": round(ema26[-1], 2) if ema26 else None,
            "macd": macd_value,
            "avg_volume20": round(avg_volume20, 2) if avg_volume20 else None,
            "relative_volume": round(relative_volume, 2) if relative_volume is not None else None,
        },
        "entry": entry,
        "stop": stop,
        "target1": target1,
        "target2": target2,
        "risk_reward": risk_reward,
        "method": "heuristic technical screen; not a return probability or guarantee",
    }


def main():
    live = json.loads(LIVE_PATH.read_text(encoding="utf-8"))
    stocks = live.get("stocks", [])
    # Fail closed until the source has passed an independent provider comparison.
    verified = (live.get("sourceVerification") or {}).get("status") == "verified"
    enabled = live.get("tradeSignalsEnabled") is True and verified
    if not enabled:
        output = {
            "schemaVersion": 3,
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "sourceUpdatedAt": live.get("sourceUpdatedAt"),
            "source": live.get("source"),
            "status": "LOCKED_UNVERIFIED_SOURCE",
            "engine": "NEPSE Pulse fail-closed screening engine",
            "warning": "No BUY/SELL/WATCH calls are published. The source has not passed independent provider verification.",
            "counts": {"stocks_scored": 0, "buy_confirmation": 0, "watch_breakout": 0, "wait": 0, "avoid": 0, "sell_review": 0},
            "signals": [], "topBuy": [], "topWatch": [], "topSell": [], "topAvoid": []
        }
        OUT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
        print("Signals locked: source is not independently verified")
        return
    signals = [result for stock in stocks if isinstance(stock, dict) for result in [score_stock(stock)] if result]
    priority = {"BUY ON CONFIRMATION": 0, "WATCH BREAKOUT": 1, "WAIT": 2, "AVOID": 3, "SELL / REDUCE (REVIEW HOLDING)": 4}
    signals.sort(key=lambda x: (priority.get(x["action"], 9), -x["score"], -(x.get("turnover") or 0)))
    output = {
        "schemaVersion": 2,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "sourceUpdatedAt": live.get("sourceUpdatedAt"),
        "source": live.get("source"),
        "engine": "NEPSE Pulse technical screener v2",
        "warning": "Heuristic screening only. No profit probability is claimed. SELL/REDUCE is not a short-selling instruction.",
        "counts": {
            "stocks_scored": len(signals),
            "buy_confirmation": sum(s["action"] == "BUY ON CONFIRMATION" for s in signals),
            "watch_breakout": sum(s["action"] == "WATCH BREAKOUT" for s in signals),
            "wait": sum(s["action"] == "WAIT" for s in signals),
            "avoid": sum(s["action"] == "AVOID" for s in signals),
            "sell_review": sum(s["action"].startswith("SELL") for s in signals),
        },
        "signals": signals,
        "topBuy": [s for s in signals if s["action"] == "BUY ON CONFIRMATION"][:10],
        "topWatch": [s for s in signals if s["action"] == "WATCH BREAKOUT"][:10],
        "topSell": [s for s in signals if s["action"].startswith("SELL")][:10],
        "topAvoid": [s for s in signals if s["action"] == "AVOID"][:10],
    }
    OUT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Scored {len(signals)} stocks; {output['counts']}")


if __name__ == "__main__":
    main()
