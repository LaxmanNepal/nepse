import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; errors=[]
for rel in ["data/live.json","data/index-history.json","data/news.json","data/ipos.json","data/status.json","data/sectors.json"]:
 p=ROOT/rel
 if not p.exists(): errors.append(f"Missing {rel}"); continue
 try: json.loads(p.read_text(encoding='utf-8'))
 except Exception as exc: errors.append(f"Invalid JSON {rel}: {exc}")
stock_root=ROOT/'stock'
if stock_root.exists():
 for p in stock_root.glob('*/data.json'):
  try:
   obj=json.loads(p.read_text(encoding='utf-8'))
   if not isinstance(obj,dict): errors.append(f"Invalid stock object: {p}"); continue
   if not obj.get('symbol'): errors.append(f"Missing symbol: {p}")
   t=obj.get('technical')
   if not isinstance(t,dict): errors.append(f"Missing technical payload: {p}")
   if not isinstance(obj.get('history'),list): errors.append(f"Missing history: {p}")
  except Exception as exc: errors.append(f"Invalid JSON {p}: {exc}")
if errors:
 print('SITE VALIDATION FAILED')
 for e in errors: print('-',e)
 raise SystemExit(1)
print('SITE VALIDATION PASSED')
