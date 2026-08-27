#!/usr/bin/env python3
import csv, io, json, pathlib, urllib.request
from datetime import date, timedelta
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'data/history/2026-08.json'
BASE='https://raw.githubusercontent.com/OmitNomis/ShareSansarScraper/master/docs/Data/'
START=date(2026,8,1); TODAY=date.today()
def get_csv(day):
    req=urllib.request.Request(BASE+day.strftime('%Y_%m_%d.csv'),headers={'User-Agent':'NEPSE-Pulse/4.0'})
    with urllib.request.urlopen(req,timeout=60) as r:return r.read().decode('utf-8-sig')
def num(v):
    s=str(v or '').strip().replace(',','')
    if not s or s in {'-','—','N/A'}: return None
    try:return float(s)
    except ValueError:return None
def normalize(row):
    out={}
    for k,v in row.items():
        key=k.strip().lower().replace(' ','_').replace('%','pct')
        if key in {'s.no','s_no'}: out['sno']=int(num(v) or 0)
        elif key=='symbol': out['symbol']=str(v or '').strip().upper()
        elif key=='conf.': out['conf']=num(v)
        else:
            n=num(v); out[key.replace('.','')]=n if n is not None else str(v or '').strip()
    return out
sessions=[]; missing=[]; cur=START
while cur<=TODAY:
    if cur.weekday()<5:
        try:
            rows=[normalize(r) for r in csv.DictReader(io.StringIO(get_csv(cur)))]
            rows=[r for r in rows if r.get('symbol')]
            if rows:sessions.append({'date':cur.isoformat(),'source':BASE+cur.strftime('%Y_%m_%d.csv'),'count':len(rows),'stocks':rows});print(cur,len(rows))
            else:missing.append(cur.isoformat())
        except Exception as exc: missing.append(cur.isoformat()); print('missing',cur,exc)
    cur+=timedelta(days=1)
if not sessions: raise SystemExit('No August 2026 sessions downloaded')
OUT.parent.mkdir(parents=True,exist_ok=True)
payload={'month':'2026-08','from':START.isoformat(),'to':TODAY.isoformat(),'source':'OmitNomis/ShareSansarScraper (ShareSansar-derived unofficial archive)','generatedAt':date.today().isoformat(),'sessions':sessions,'missingSessions':missing,'sessionCount':len(sessions),'symbolCountLatest':sessions[-1]['count']}
OUT.write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
print('Wrote',OUT,'sessions=',len(sessions),'latest=',sessions[-1]['count'],'missing=',missing)
