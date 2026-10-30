import datetime
import json
import pathlib
import re
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
BASE_SOURCE = "https://shubhamnpk.github.io/yonepse/data/"
SOURCE = BASE_SOURCE + "market/live.json"
INDEX_SOURCE = BASE_SOURCE + "market/indices.json"
PROFILES_SOURCE = BASE_SOURCE + "company/profiles.json"
FINANCIALS_SOURCE = BASE_SOURCE + "company/financials.json"
TEMPLATE = ROOT / "stock" / "_template" / "research.html"
LIVE = ROOT / "data" / "live.json"
INDEX_HISTORY = ROOT / "data" / "index-history.json"
NEWS = ROOT / "data" / "news.json"
SECTORS = ROOT / "data" / "sectors.json"
COMPANY_DATA = ROOT / "data" / "companies.json"


def load_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "NEPSE-Pulse/3.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def rows(payload):
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("data", "stocks", "items", "rows", "companies"):
            if isinstance(payload.get(key), list):
                return payload[key]
    return []


def symbol(stock):
    return str(stock.get("symbol") or stock.get("ticker") or stock.get("securitySymbol") or "").strip().upper()


def name(stock):
    return stock.get("name") or stock.get("companyName") or stock.get("company") or stock.get("securityName") or symbol(stock)


def price(stock):
    try:
        return float(stock.get("ltp") or stock.get("lastTradedPrice") or stock.get("lastPrice") or stock.get("price") or 0)
    except (TypeError, ValueError):
        return 0.0


def sma(values, n):
    return sum(values[-n:]) / n if len(values) >= n else None


def ema(values, n):
    if len(values) < n:
        return None
    k = 2 / (n + 1)
    value = sum(values[:n]) / n
    for v in values[n:]:
        value = v * k + value * (1 - k)
    return value


def rsi(values, n=14):
    if len(values) <= n:
        return None
    gains, losses = [], []
    for i in range(1, len(values)):
        d = values[i] - values[i - 1]
        gains.append(max(d, 0))
        losses.append(max(-d, 0))
    ag, al = sum(gains[-n:]) / n, sum(losses[-n:]) / n
    if al == 0:
        return 100.0
    return 100 - (100 / (1 + ag / al))


def macd(values):
    if len(values) < 26:
        return None
    e12, e26 = ema(values, 12), ema(values, 26)
    return e12 - e26 if e12 is not None and e26 is not None else None


def technical(values):
    if not values:
        return {"score": None, "signal": "NEUTRAL", "rsi": None, "sma20": None, "sma50": None, "sma200": None, "ema20": None, "macd": None, "reasons": [], "risks": []}
    last = values[-1]
    s20, s50, s200, e20, rv, mc = sma(values, 20), sma(values, 50), sma(values, 200), ema(values, 20), rsi(values), macd(values)
    score, reasons, risks = 50, [], []
    for val, weight, label in ((s20, 12, "SMA20"), (s50, 12, "SMA50"), (s200, 10, "SMA200")):
        if val is not None:
            if last > val:
                score += weight; reasons.append(f"Price above {label}")
            else:
                score -= weight; risks.append(f"Price below {label}")
    if rv is not None:
        if 50 <= rv <= 70:
            score += 10; reasons.append("RSI supports momentum")
        elif rv > 75:
            score -= 8; risks.append("RSI is overbought")
        elif rv < 30:
            score += 5; reasons.append("RSI is oversold")
    if mc is not None:
        if mc > 0:
            score += 6; reasons.append("MACD positive")
        else:
            score -= 6; risks.append("MACD negative")
    score = max(0, min(100, score))
    signal = "BULLISH" if score >= 70 else "BEARISH" if score <= 35 else "NEUTRAL"
    return {"score": score, "signal": signal, "rsi": round(rv, 2) if rv is not None else None, "sma20": round(s20, 2) if s20 else None, "sma50": round(s50, 2) if s50 else None, "sma200": round(s200, 2) if s200 else None, "ema20": round(e20, 2) if e20 else None, "macd": round(mc, 4) if mc is not None else None, "reasons": reasons[:5], "risks": risks[:5]}


def keyed(items):
    out = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        s = symbol(item)
        if s:
            out[s] = item
    return out


payload = load_json(SOURCE)
stocks = rows(payload)
now = datetime.datetime.now(datetime.timezone.utc)
nepal = now.astimezone(datetime.timezone(datetime.timedelta(hours=5, minutes=45)))
valid = [s for s in stocks if re.fullmatch(r"[A-Z0-9._-]{1,20}", symbol(s))]
if not valid:
    raise RuntimeError("No valid stocks returned by the market source; refusing to overwrite site data")

LIVE.parent.mkdir(parents=True, exist_ok=True)
LIVE.write_text(json.dumps({"updatedAt": now.isoformat(), "source": SOURCE, "stocks": valid}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

profiles = {}
financials = {}
try:
    profiles = keyed(rows(load_json(PROFILES_SOURCE)))
except Exception as exc:
    print(f"Company profiles unavailable: {exc}")
try:
    financials = keyed(rows(load_json(FINANCIALS_SOURCE)))
except Exception as exc:
    print(f"Company financials unavailable: {exc}")

company_index = {}
for s in valid:
    sym = symbol(s)
    profile = profiles.get(sym, {})
    financial = financials.get(sym, {})
    company_index[sym] = {"symbol": sym, "name": name(s), "sector": s.get("sector") or s.get("sectorName") or profile.get("sector") or "Other", "profile": profile, "financials": financial}
COMPANY_DATA.write_text(json.dumps({"updatedAt": now.isoformat(), "source": {"profiles": PROFILES_SOURCE, "financials": FINANCIALS_SOURCE}, "companies": company_index}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

try:
    index_payload = load_json(INDEX_SOURCE)
    index_rows = rows(index_payload)
    nepse = next((x for x in index_rows if "nepse" in str(x.get("index", x.get("name", ""))).lower()), None)
    if nepse:
        history = json.loads(INDEX_HISTORY.read_text(encoding="utf-8")) if INDEX_HISTORY.exists() else {"index": "NEPSE", "points": []}
        points = history.get("points", [])
        point = {"date": f"{nepal:%Y-%m-%d}", "timestamp": now.isoformat(), "value": float(nepse.get("currentValue", nepse.get("close", 0)) or 0), "change": float(nepse.get("change", 0) or 0), "percent": float(nepse.get("perChange", 0) or 0), "high": float(nepse.get("high", 0) or 0), "low": float(nepse.get("low", 0) or 0)}
        if point["value"] > 0:
            minute = point["timestamp"][:16]
            points = [p for p in points if str(p.get("timestamp", ""))[:16] != minute]
            points.append(point)
            points = sorted(points, key=lambda p: (p.get("date", ""), p.get("timestamp", "")))[-100000:]
            history.update({"updatedAt": now.isoformat(), "source": INDEX_SOURCE, "points": points})
            INDEX_HISTORY.write_text(json.dumps(history, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
except Exception as exc:
    print(f"Index history update skipped: {exc}")

day_dir = ROOT / "data" / "intraday"
day_dir.mkdir(parents=True, exist_ok=True)
day_file = day_dir / f"{nepal:%Y-%m-%d}.json"
try:
    day = json.loads(day_file.read_text(encoding="utf-8")) if day_file.exists() else {"date": f"{nepal:%Y-%m-%d}", "snapshots": []}
except Exception:
    day = {"date": f"{nepal:%Y-%m-%d}", "snapshots": []}
snapshot = {"timestamp": now.isoformat(), "nepalDate": f"{nepal:%Y-%m-%d}", "stocks": valid}
minute_key = now.strftime("%Y-%m-%dT%H:%M")
if not any(str(x.get("timestamp", ""))[:16] == minute_key for x in day["snapshots"][-3:]):
    day["snapshots"].append(snapshot)
day["snapshots"] = day["snapshots"][-500:]
day_file.write_text(json.dumps(day, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

tpl = TEMPLATE.read_text(encoding="utf-8")
try:
    news = json.loads(NEWS.read_text(encoding="utf-8"))
except Exception:
    news = []
sector_map = {}
for stock in valid:
    s = symbol(stock)
    company_history = []
    for snap in day["snapshots"]:
        match = next((x for x in snap.get("stocks", []) if symbol(x) == s), None)
        if match:
            company_history.append({"timestamp": snap["timestamp"], "stock": match})
    values = [price(x.get("stock") or x) for x in company_history]
    values = [v for v in values if v > 0]
    analysis = technical(values)
    related = [x for x in news if s in [str(v).upper() for v in x.get("symbols", [])]][:12]
    sector = str(stock.get("sector") or stock.get("sectorName") or profiles.get(s, {}).get("sector") or "Other").strip() or "Other"
    sm = sector_map.setdefault(sector, {"sector": sector, "count": 0, "volume": 0, "turnover": 0, "gainers": 0, "losers": 0, "unchanged": 0})
    sm["count"] += 1
    sm["volume"] += float(stock.get("volume") or stock.get("totalTradedQuantity") or 0)
    sm["turnover"] += float(stock.get("turnover") or stock.get("totalTradedValue") or 0)
    ch = float(stock.get("change") or stock.get("pointChange") or 0)
    sm["gainers"] += ch > 0; sm["losers"] += ch < 0; sm["unchanged"] += ch == 0
    out = ROOT / "stock" / s.lower()
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(tpl, encoding="utf-8")
    company_payload = {"symbol": s, "name": name(stock), "generatedAt": now.isoformat(), "marketDateNepal": f"{nepal:%Y-%m-%d}", "stock": stock, "profile": profiles.get(s, {}), "financials": financials.get(s, {}), "history": company_history, "technical": analysis, "news": related}
    (out / "data.json").write_text(json.dumps(company_payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

SECTORS.write_text(json.dumps({"updatedAt": now.isoformat(), "sectors": list(sector_map.values())}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print(f"Generated {len(valid)} company pages; embedded {len(profiles)} profiles and {len(financials)} financial records across {len(sector_map)} sectors at {nepal.isoformat()}")
