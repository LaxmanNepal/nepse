#!/usr/bin/env python3
"""Generate one canonical research page per listed NEPSE symbol.

Routes are /stock/<lowercase-symbol>/ and every page shares the same template/UI.
A company-specific data.json is emitted beside the page so static hosting works.
"""
from __future__ import annotations
import json, os, re, shutil
from pathlib import Path
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'stock'
TEMPLATE=OUT/'_template'/'index.html'
DATA_URL='https://raw.githubusercontent.com/yonepse/nepse-data/main/nepse_data.json'

def get_json(url):
    req=Request(url,headers={'User-Agent':'NEPSE-Pulse/1.0'})
    with urlopen(req,timeout=30) as r: return json.loads(r.read().decode('utf-8'))

def clean_symbol(v):
    return re.sub(r'[^A-Za-z0-9_-]','',str(v or '')).lower()

def main():
    raw=get_json(DATA_URL)
    stocks=raw if isinstance(raw,list) else raw.get('stocks') or raw.get('data') or []
    if not stocks: raise RuntimeError('No stock records received')
    template=TEMPLATE.read_text(encoding='utf-8')
    generated=0
    for stock in stocks:
        symbol=str(stock.get('symbol') or stock.get('Symbol') or '').strip().upper()
        if not symbol: continue
        slug=clean_symbol(symbol)
        if not slug: continue
        dest=OUT/slug
        dest.mkdir(parents=True,exist_ok=True)
        (dest/'index.html').write_text(template,encoding='utf-8')
        payload={**stock,'symbol':symbol}
        (dest/'data.json').write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
        generated+=1
    print(f'Generated {generated} stock routes')

if __name__=='__main__': main()
