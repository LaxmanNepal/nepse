#!/usr/bin/env python3
import csv,io,json,pathlib,urllib.request
from datetime import date,timedelta
ROOT=pathlib.Path(__file__).resolve().parents[1];OUT=ROOT/'data/history/2026-08.json';BASE='https://raw.githubusercontent.com/OmitNomis/ShareSansarScraper/master/docs/Data/';LIVE='https://shubhamnpk.github.io/yonepse/data/market/live.json';START=date(2026,8,1);TODAY=date.today()
def text(url):
 r=urllib.request.Request(url,headers={'User-Agent':'NEPSE-Pulse/4.0'});return urllib.request.urlopen(r,timeout=60).read()
def num(v):
 s=str(v or '').strip().replace(',','')
 if not s or s in {'-','—','N/A'}:return None
 try:return float(s)
 except:return None
def normalize(row):
 out={}
 for k,v in row.items():
  key=k.strip().lower().replace(' ','_').replace('%','pct')
  if key in {'s.no','s_no'}:out['sno']=int(num(v) or 0)
  elif key=='symbol':out['symbol']=str(v or '').strip().upper()
  elif key=='conf.':out['conf']=num(v)
  else:
   n=num(v);out[key.replace('.','')]=n if n is not None else str(v or '').strip()
 return out
def live_rows(raw):
 rows=raw if isinstance(raw,list) else raw.get('stocks',raw.get('data',[]))
 out=[]
 for i,x in enumerate(rows,1):
  sym=str(x.get('symbol') or x.get('ticker') or x.get('securitySymbol') or '').upper()
  if not sym:continue
  def g(*ks):
   for k in ks:
    if k in x:return x[k]
   return None
  out.append({'sno':i,'symbol':sym,'open':num(g('open')),'high':num(g('high')),'low':num(g('low')),'close':num(g('close','ltp','lastPrice')),'ltp':num(g('ltp','lastTradedPrice','lastPrice')),'vwap':num(g('vwap')),'vol':num(g('volume','totalTradedQuantity')),'prev_close':num(g('previous_close','previousClose')),'turnover':num(g('turnover','totalTradedValue')),'trans':num(g('transactions','transactionCount')),'diff':num(g('change','pointChange')),'diff_pct':num(g('percent_change','percentChange','percentageChange'))})
 return out
sessions=[];missing=[];cur=START
while cur<=TODAY:
 if cur.weekday()<5:
  try:
   rows=[normalize(r) for r in csv.DictReader(io.StringIO(text(BASE+cur.strftime('%Y_%m_%d.csv')).decode('utf-8-sig')))];rows=[r for r in rows if r.get('symbol')]
   if rows:sessions.append({'date':cur.isoformat(),'source':BASE+cur.strftime('%Y_%m_%d.csv'),'count':len(rows),'stocks':rows});print(cur,len(rows))
   else:missing.append(cur.isoformat())
  except Exception as exc:
   if cur==TODAY:
    try:
     rows=live_rows(json.loads(text(LIVE).decode('utf-8')))
     if rows:sessions.append({'date':cur.isoformat(),'source':LIVE,'count':len(rows),'stocks':rows});print(cur,'live',len(rows))
     else:missing.append(cur.isoformat())
    except Exception as exc2:missing.append(cur.isoformat());print('missing',cur,exc,exc2)
   else:missing.append(cur.isoformat());print('missing',cur,exc)
 cur+=timedelta(days=1)
if not sessions:raise SystemExit('No August 2026 sessions downloaded')
sessions.sort(key=lambda x:x['date']);OUT.parent.mkdir(parents=True,exist_ok=True)
payload={'month':'2026-08','from':START.isoformat(),'to':TODAY.isoformat(),'source':'OmitNomis/ShareSansarScraper plus current NEPSE live feed for the latest session','generatedAt':date.today().isoformat(),'sessions':sessions,'missingSessions':missing,'sessionCount':len(sessions),'symbolCountLatest':sessions[-1]['count']}
OUT.write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')),encoding='utf-8');print('Wrote',OUT,'sessions=',len(sessions),'latest=',sessions[-1]['count'],'missing=',missing)
