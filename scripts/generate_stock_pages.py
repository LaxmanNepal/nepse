import datetime
import json
import math
import pathlib
import re
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = "https://shubhamnpk.github.io/yonepse/data/nepse_data.json"
INDEX_SOURCE = "https://shubhamnpk.github.io/yonepse/data/market/indices.json"
TEMPLATE = ROOT / "stock" / "_template" / "research.html"
LIVE = ROOT / "data" / "live.json"
INDEX_HISTORY = ROOT / "data" / "index-history.json"
NEWS = ROOT / "data" / "news.json"
SECTORS = ROOT / "data" / "sectors.json"

def load_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "NEPSE-Pulse/2.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def symbol(stock):
    return str(stock.get("symbol") or stock.get("ticker") or stock.get("securitySymbol") or "").strip().upper()

def name(stock):
    return stock.get("name") or stock.get("companyName") or stock.get("company") or stock.get("securityName") or symbol(stock)

def price(stock):
    return float(stock.get("ltp") or stock.get("lastTradedPrice") or stock.get("lastPrice") or 0)

def sma(values, n):
    if len(values) < n: return None
    return sum(values[-n:]) / n

def ema(values, n):
    if len(values) < n: return None
    k = 2 / (n + 1); value = sum(values[:n]) / n
    for v in values[n:]: value = v * k + value * (1-k)
    return value

def rsi(values, n=14):
    if len(values) <= n: return None
    gains=[]; losses=[]
    for i in range(1,len(values)):
        d=values[i]-values[i-1]; gains.append(max(d,0)); losses.append(max(-d,0))
    ag=sum(gains[-n:])/n; al=sum(losses[-n:])/n
    if al == 0: return 100.0
    return 100 - (100/(1+ag/al))

def macd(values):
    if len(values) < 26: return None
    e12=ema(values,12); e26=ema(values,26)
    return e12-e26 if e12 is not None and e26 is not None else None

def technical(values):
    if not values: return {"score": None,"signal":"HOLD","rsi":None,"sma20":None,"sma50":None,"sma200":None,"ema20":None,"macd":None}
    last=values[-1]; s20=sma(values,20); s50=sma(values,50); s200=sma(values,200); e20=ema(values,20); rv=rsi(values); mc=macd(values)
    score=50; reasons=[]; risks=[]
    if s20:
        if last>s20: score+=12; reasons.append("Price above SMA20")
        else: score-=12; risks.append("Price below SMA20")
    if s50:
        if last>s50: score+=12; reasons.append("Price above SMA50")
        else: score-=12; risks.append("Price below SMA50")
    if s200:
        if last>s200: score+=10; reasons.append("Price above SMA200")
        else: score-=10; risks.append("Price below SMA200")
    if rv is not None:
        if 50<=rv<=70: score+=10; reasons.append("RSI supports momentum")
        elif rv>75: score-=8; risks.append("RSI is overbought")
        elif rv<30: score+=5; reasons.append("RSI is oversold")
        else: score-=3
    if mc is not None:
        if mc>0: score+=6; reasons.append("MACD positive")
        else: score-=6; risks.append("MACD negative")
    score=max(0,min(100,score)); signal="BUY" if score>=70 else "SELL" if score<=35 else "HOLD"
    return {"score":score,"signal":signal,"rsi":round(rv,2) if rv is not None else None,"sma20":round(s20,2) if s20 else None,"sma50":round(s50,2) if s50 else None,"sma200":round(s200,2) if s200 else None,"ema20":round(e20,2) if e20 else None,"macd":round(mc,4) if mc is not None else None,"reasons":reasons[:5],"risks":risks[:5]}

payload = load_json(SOURCE)
stocks = payload if isinstance(payload, list) else payload.get("data", payload.get("stocks", []))
now = datetime.datetime.now(datetime.timezone.utc)
nepal = now.astimezone(datetime.timezone(datetime.timedelta(hours=5, minutes=45)))
LIVE.parent.mkdir(parents=True, exist_ok=True)
LIVE.write_text(json.dumps({"updatedAt": now.isoformat(), "source": SOURCE, "stocks": stocks}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

try:
    index_payload = load_json(INDEX_SOURCE)
    index_rows = index_payload if isinstance(index_payload, list) else index_payload.get("items", index_payload.get("data", []))
    nepse = next((x for x in index_rows if "nepse" in str(x.get("index", x.get("name", ""))).lower()), None)
    if nepse:
        index_history = json.loads(INDEX_HISTORY.read_text(encoding="utf-8")) if INDEX_HISTORY.exists() else {"index": "NEPSE", "points": []}
        points = index_history.get("points", [])
        point = {"date":f"{nepal:%Y-%m-%d}","timestamp":now.isoformat(),"value":float(nepse.get("currentValue",nepse.get("close",0)) or 0),"change":float(nepse.get("change",0) or 0),"percent":float(nepse.get("perChange",0) or 0),"high":float(nepse.get("high",0) or 0),"low":float(nepse.get("low",0) or 0)}
        if point["value"] > 0:
            minute=point["timestamp"][:16]; points=[p for p in points if str(p.get("timestamp",""))[:16]!=minute]; points.append(point); points=sorted(points,key=lambda p:(p.get("date",""),p.get("timestamp","")))[-100000:]
            index_history.update({"updatedAt":now.isoformat(),"source":INDEX_SOURCE,"points":points}); INDEX_HISTORY.write_text(json.dumps(index_history,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
except Exception as exc: print(f"Index history update skipped: {exc}")

day_dir=ROOT/"data"/"intraday"; day_dir.mkdir(parents=True,exist_ok=True); day_file=day_dir/f"{nepal:%Y-%m-%d}.json"
try: day=json.loads(day_file.read_text(encoding="utf-8")) if day_file.exists() else {"date":f"{nepal:%Y-%m-%d}","snapshots":[]}
except Exception: day={"date":f"{nepal:%Y-%m-%d}","snapshots":[]}
snapshot={"timestamp":now.isoformat(),"nepalDate":f"{nepal:%Y-%m-%d}","stocks":stocks}; minute_key=now.strftime("%Y-%m-%dT%H:%M")
if not any(str(x.get("timestamp",""))[:16]==minute_key for x in day["snapshots"][-3:]): day["snapshots"].append(snapshot)
day["snapshots"]=day["snapshots"][-500:]; day_file.write_text(json.dumps(day,ensure_ascii=False,separators=(",",":")),encoding="utf-8")

tpl=TEMPLATE.read_text(encoding="utf-8"); valid=[s for s in stocks if re.fullmatch(r"[A-Z0-9._-]{1,20}",symbol(s))]
news=[]
try: news=json.loads(NEWS.read_text(encoding="utf-8"))
except Exception: pass
sector_map={}
for stock in valid:
    s=symbol(stock); company_history=[]
    for snap in day["snapshots"]:
        match=next((x for x in snap.get("stocks",[]) if symbol(x)==s),None)
        if match: company_history.append({"timestamp":snap["timestamp"],"stock":match})
    values=[price((x.get("stock") or x)) for x in company_history]; values=[v for v in values if v>0]
    analysis=technical(values)
    related=[x for x in news if s in [str(v).upper() for v in x.get("symbols",[])]][:12]
    sector=str(stock.get("sector") or stock.get("sectorName") or "Other").strip() or "Other"
    sector_map.setdefault(sector,{"sector":sector,"count":0,"volume":0,"turnover":0,"gainers":0,"losers":0,"unchanged":0})
    sm=sector_map[sector]; sm["count"]+=1; sm["volume"]+=float(stock.get("volume") or stock.get("totalTradedQuantity") or 0); sm["turnover"]+=float(stock.get("turnover") or stock.get("totalTradedValue") or 0)
    ch=float(stock.get("change") or stock.get("pointChange") or 0); sm["gainers"]+=ch>0; sm["losers"]+=ch<0; sm["unchanged"]+=ch==0
    out=ROOT/"stock"/s.lower(); out.mkdir(parents=True,exist_ok=True); (out/"index.html").write_text(tpl,encoding="utf-8")
    company_payload={"symbol":s,"name":name(stock),"generatedAt":now.isoformat(),"marketDateNepal":f"{nepal:%Y-%m-%d}","stock":stock,"history":company_history,"technical":analysis,"news":related}
    (out/"data.json").write_text(json.dumps(company_payload,ensure_ascii=False,separators=(",",":")),encoding="utf-8")

SECTORS.write_text(json.dumps({"updatedAt":now.isoformat(),"sectors":list(sector_map.values())},ensure_ascii=False,separators=(",",":")),encoding="utf-8")
print(f"Generated {len(valid)} company research pages with technical analysis/news and {len(sector_map)} sectors at {nepal.isoformat()}")
