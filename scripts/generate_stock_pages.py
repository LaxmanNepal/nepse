import json,pathlib,re,urllib.request,datetime
ROOT=pathlib.Path(__file__).resolve().parents[1];SOURCE='https://shubhamnpk.github.io/yonepse/data/nepse_data.json';TEMPLATE=ROOT/'stock/_template/index.html';out=ROOT/'data/live.json';out.parent.mkdir(parents=True,exist_ok=True)
with urllib.request.urlopen(SOURCE,timeout=30) as r:data=json.load(r)
stocks=data if isinstance(data,list) else data.get('data',data.get('stocks',[]));out.write_text(json.dumps({'updatedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'stocks':stocks},ensure_ascii=False,separators=(',',':')),encoding='utf-8');tpl=TEMPLATE.read_text(encoding='utf-8')
for s in stocks:
 sym=str(s.get('symbol') or s.get('ticker') or s.get('securitySymbol') or '').strip().lower()
 if re.fullmatch(r'[a-z0-9._-]{1,20}',sym):
  p=ROOT/'stock'/sym/'index.html';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(tpl,encoding='utf-8')
print('Generated',len(stocks),'stock routes')
