import datetime
import json
import pathlib
import re
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = "https://shubhamnpk.github.io/yonepse/data/nepse_data.json"
TEMPLATE = ROOT / "stock" / "_template" / "index.html"
LIVE = ROOT / "data" / "live.json"

with urllib.request.urlopen(SOURCE, timeout=30) as r:
    payload = json.load(r)

stocks = payload if isinstance(payload, list) else payload.get("data", payload.get("stocks", []))
now = datetime.datetime.now(datetime.timezone.utc)
LIVE.parent.mkdir(parents=True, exist_ok=True)
LIVE.write_text(json.dumps({"updatedAt": now.isoformat(), "stocks": stocks}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

# One compact daily file is easier for a static site to consume than thousands of tiny files.
nepal = now.astimezone(datetime.timezone(datetime.timedelta(hours=5, minutes=45)))
day_dir = ROOT / "data" / "intraday"
day_dir.mkdir(parents=True, exist_ok=True)
day_file = day_dir / f"{nepal:%Y-%m-%d}.json"
try:
    day = json.loads(day_file.read_text(encoding="utf-8")) if day_file.exists() else {"date": f"{nepal:%Y-%m-%d}", "snapshots": []}
except Exception:
    day = {"date": f"{nepal:%Y-%m-%d}", "snapshots": []}

snapshot = {"timestamp": now.isoformat(), "nepalDate": f"{nepal:%Y-%m-%d}", "stocks": stocks}
if not any(x.get("timestamp") == snapshot["timestamp"] for x in day["snapshots"][-3:]):
    day["snapshots"].append(snapshot)
day["snapshots"] = day["snapshots"][-500:]
day_file.write_text(json.dumps(day, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

tpl = TEMPLATE.read_text(encoding="utf-8")
count = 0
for s in stocks:
    sym = str(s.get("symbol") or s.get("ticker") or s.get("securitySymbol") or "").strip().lower()
    if re.fullmatch(r"[a-z0-9._-]{1,20}", sym):
        p = ROOT / "stock" / sym / "index.html"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(tpl, encoding="utf-8")
        count += 1

print(f"Generated {count} stock routes; stored snapshot {nepal.isoformat()}")
