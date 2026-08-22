"""Validate generated NEPSE market data before deployment."""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
LIVE = ROOT / "data" / "live.json"
INDEX = ROOT / "data" / "index-history.json"

errors = []

if not LIVE.exists():
    errors.append("data/live.json is missing")
else:
    try:
        payload = json.loads(LIVE.read_text(encoding="utf-8"))
        stocks = payload.get("stocks", []) if isinstance(payload, dict) else []
        if not stocks:
            errors.append("data/live.json contains no stocks")
        symbols = set()
        for stock in stocks:
            symbol = str(stock.get("symbol") or stock.get("ticker") or stock.get("securitySymbol") or "").strip().upper()
            if not symbol:
                errors.append("stock without symbol")
                continue
            if symbol in symbols:
                errors.append(f"duplicate symbol: {symbol}")
            symbols.add(symbol)
            for key in ("ltp", "lastTradedPrice", "lastPrice", "price"):
                if key in stock and stock[key] not in (None, ""):
                    try:
                        if float(stock[key]) < 0:
                            errors.append(f"negative price: {symbol}")
                    except (TypeError, ValueError):
                        errors.append(f"invalid price: {symbol}")
                    break

if INDEX.exists():
    try:
        history = json.loads(INDEX.read_text(encoding="utf-8"))
        if not isinstance(history.get("points", []), list):
            errors.append("index-history points is not a list")
    except Exception as exc:
        errors.append(f"invalid index-history.json: {exc}")

if errors:
    print("MARKET DATA VALIDATION FAILED")
    for error in errors[:50]:
        print(f"- {error}")
    sys.exit(1)

print("MARKET DATA VALIDATION PASSED")
