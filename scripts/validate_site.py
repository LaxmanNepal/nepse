import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
errors = []

required = [
    "data/live.json", "data/index-history.json", "data/news.json", "data/ipos.json",
    "data/status.json", "data/sectors.json", "data/companies.json"
]
for rel in required:
    p = ROOT / rel
    if not p.exists():
        errors.append(f"Missing {rel}")
        continue
    try:
        json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"Invalid JSON {rel}: {exc}")

live = ROOT / "data/live.json"
if live.exists():
    try:
        payload = json.loads(live.read_text(encoding="utf-8"))
        stocks = payload.get("stocks", []) if isinstance(payload, dict) else []
        if not stocks:
            errors.append("data/live.json contains no stocks")
        if len(stocks) < 100:
            errors.append(f"Suspiciously low stock count: {len(stocks)}")
        updated = payload.get("updatedAt")
        if updated:
            try:
                age = (datetime.now(timezone.utc) - datetime.fromisoformat(updated.replace("Z", "+00:00"))).total_seconds()
                if age > 24 * 3600:
                    errors.append(f"Market data is stale: {round(age / 3600, 1)} hours old")
            except ValueError:
                errors.append("Invalid live.json updatedAt timestamp")
        symbols = set()
        for stock in stocks:
            symbol = str(stock.get("symbol") or stock.get("ticker") or stock.get("securitySymbol") or "").strip().upper()
            if not re.fullmatch(r"[A-Z0-9._-]{1,20}", symbol):
                errors.append(f"Invalid stock symbol: {symbol or '<empty>'}")
                continue
            if symbol in symbols:
                errors.append(f"duplicate symbol: {symbol}")
            symbols.add(symbol)
            price = stock.get("ltp", stock.get("lastTradedPrice", stock.get("lastPrice", stock.get("price"))))
            if price not in (None, ""):
                try:
                    if float(price) < 0:
                        errors.append(f"negative price: {symbol}")
                except (TypeError, ValueError):
                    errors.append(f"invalid price: {symbol}")
    except Exception as exc:
        errors.append(f"Unable to validate live.json: {exc}")

companies = ROOT / "data/companies.json"
if companies.exists():
    try:
        obj = json.loads(companies.read_text(encoding="utf-8"))
        if not isinstance(obj.get("companies"), dict) or not obj["companies"]:
            errors.append("data/companies.json contains no company records")
    except Exception as exc:
        errors.append(f"Invalid companies.json: {exc}")

stock_root = ROOT / "stock"
if stock_root.exists():
    pages = list(stock_root.glob("*/data.json"))
    if len(pages) < 100:
        errors.append(f"Too few generated stock pages: {len(pages)}")
    for p in pages:
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
            if not isinstance(obj, dict):
                errors.append(f"Invalid stock object: {p}")
                continue
            for key in ("symbol", "stock", "profile", "financials", "technical", "history", "news"):
                if key not in obj:
                    errors.append(f"Missing {key}: {p}")
            if not isinstance(obj.get("technical"), dict):
                errors.append(f"Invalid technical payload: {p}")
            if not isinstance(obj.get("history"), list):
                errors.append(f"Invalid history: {p}")
        except Exception as exc:
            errors.append(f"Invalid JSON {p}: {exc}")

if errors:
    print("SITE VALIDATION FAILED")
    for error in errors[:100]:
        print("-", error)
    raise SystemExit(1)

print(f"SITE VALIDATION PASSED — {len(list((ROOT / 'stock').glob('*/data.json')))} stock pages checked")
