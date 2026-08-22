import datetime
import json
import pathlib
import re
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = "https://shubhamnpk.github.io/yonepse/data/nepse_data.json"
TEMPLATE = ROOT / "stock" / "_template" / "research.html"
LIVE = ROOT / "data" / "live.json"


def load_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "NEPSE-Pulse/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def symbol(stock):
    return str(stock.get("symbol") or stock.get("ticker") or stock.get("securitySymbol") or "").strip().upper()


def name(stock):
    return stock.get("name") or stock.get("companyName") or stock.get("company") or stock.get("securityName") or symbol(stock)

payload = load_json(SOURCE)
stocks = payload if isinstance(payload, list) else payload.get("data", payload.get("stocks", []))
now = datetime.datetime.now(datetime.timezone.utc)
nepal = now.astimezone(datetime.timezone(datetime.timedelta(hours=5, minutes=45)))

LIVE.parent.mkdir(parents=True, exist_ok=True)
LIVE.write_text(json.dumps({"updatedAt": now.isoformat(), "stocks": stocks}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

# One compact daily archive. Each snapshot contains the complete market universe.
day_dir = ROOT / "data" / "intraday"
day_dir.mkdir(parents=True, exist_ok=True)
day_file = day_dir / f"{nepal:%Y-%m-%d}.json"
try:
    day = json.loads(day_file.read_text(encoding="utf-8")) if day_file.exists() else {"date": f"{nepal:%Y-%m-%d}", "snapshots": []}
except Exception:
    day = {"date": f"{nepal:%Y-%m-%d}", "snapshots": []}

snapshot = {"timestamp": now.isoformat(), "nepalDate": f"{nepal:%Y-%m-%d}", "stocks": stocks}
# Avoid duplicate snapshots when Actions retries the same minute.
minute_key = now.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M")
if not any(str(x.get("timestamp", ""))[:16] == minute_key for x in day["snapshots"][-3:]):
    day["snapshots"].append(snapshot)
day["snapshots"] = day["snapshots"][-500:]
day_file.write_text(json.dumps(day, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

tpl = TEMPLATE.read_text(encoding="utf-8")
valid = []
for stock in stocks:
    s = symbol(stock)
    if re.fullmatch(r"[A-Z0-9._-]{1,20}", s):
        valid.append(stock)

# Generate a self-contained data file for every company. This makes /stock/<symbol>/
# a real company page rather than a generic company.html route.
for stock in valid:
    s = symbol(stock)
    company_history = []
    for snap in day["snapshots"]:
        match = next((x for x in snap.get("stocks", []) if symbol(x) == s), None)
        if match:
            company_history.append({"timestamp": snap["timestamp"], "stock": match})

    out = ROOT / "stock" / s.lower()
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(tpl, encoding="utf-8")
    company_payload = {
        "symbol": s,
        "name": name(stock),
        "generatedAt": now.isoformat(),
        "marketDateNepal": f"{nepal:%Y-%m-%d}",
        "stock": stock,
        "history": company_history,
    }
    (out / "data.json").write_text(json.dumps(company_payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

print(f"Generated {len(valid)} company pages and data files; snapshot {nepal.isoformat()}")
