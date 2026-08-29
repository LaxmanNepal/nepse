import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
errors=[]
def read(rel):
 p=ROOT/rel
 if not p.exists(): errors.append(f"Missing {rel}"); return None
 try:return json.loads(p.read_text(encoding="utf-8"))
 except Exception as e:errors.append(f"Invalid JSON {rel}: {e}");return None
live=read("data/live.json");read("data/index-history.json");read("data/news.json");read("data/ipos.json");read("data/status.json")
stocks=[]
if isinstance(live,dict):stocks=live.get("stocks") or live.get("data") or []
elif isinstance(live,list):stocks=live
if not isinstance(stocks,list) or len(stocks)<100:errors.append(f"Suspicious stock universe: {len(stocks) if isinstance(stocks,list) else 0}")
symbols=set()
for s in stocks if isinstance(stocks,list) else []:
 sym=str(s.get("symbol") or s.get("ticker") or "").strip().upper()
 if not re.fullmatch(r"[A-Z0-9._-]{1,20}",sym):errors.append(f"Invalid symbol: {sym or '<empty>'}");continue
 if sym in symbols:errors.append(f"Duplicate symbol: {sym}")
 symbols.add(sym)
 for k in ("ltp","high","low","previous_close","previousClose"):
  if k in s and s[k] not in (None,""):
   try:
    if float(s[k])<0:errors.append(f"Negative {k}: {sym}")
   except:errors.append(f"Invalid {k}: {sym}")
 high=s.get("high");low=s.get("low")
 try:
  if high is not None and low is not None and float(high)<float(low):errors.append(f"High below low: {sym}")
 except:pass
pages=list((ROOT/"stock").glob("*/data.json"))
if len(pages)<100:errors.append(f"Too few stock pages: {len(pages)}")
page_symbols={p.parent.name.upper() for p in pages}
missing=symbols-page_symbols
if missing:errors.append(f"Missing stock pages for {len(missing)} symbols: {', '.join(sorted(missing)[:15])}")
if errors:
 print("SITE VALIDATION FAILED");[print("-",x) for x in errors[:100]];raise SystemExit(1)
print(f"SITE VALIDATION PASSED — {len(symbols)} securities, {len(pages)} company datasets")
