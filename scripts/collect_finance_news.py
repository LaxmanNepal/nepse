import json, pathlib, re, urllib.request, xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
ROOT=pathlib.Path(__file__).resolve().parents[1]
REG=ROOT/'data/news-sources.json'; OUT=ROOT/'data/news.json'

def get(url):
 r=urllib.request.Request(url,headers={'User-Agent':'NEPSE-Pulse-News/1.0'})
 with urllib.request.urlopen(r,timeout=20) as x:return x.read()
def txt(e): return re.sub(r'\\s+',' ',''.join(e.itertext())).strip() if e is not None else ''
items=[]
for s in json.loads(REG.read_text())['sources']:
 urls=[s.get('feed'),s.get('rss'),s.get('atom'),s.get('sitemap')]
 for u in filter(None,urls):
  try:
   root=ET.fromstring(get(u)); ns={'a':'http://www.w3.org/2005/Atom'}
   entries=root.findall('.//item') or root.findall('.//a:entry',ns)
   for e in entries[:100]:
    title=txt(e.find('title')) or txt(e.find('a:title',ns)); link=e.findtext('link') or ''
    if not link:
     le=e.find('a:link',ns); link=le.attrib.get('href','') if le is not None else ''
    date=txt(e.find('pubDate')) or txt(e.find('a:updated',ns))
    items.append({'title':title,'url':link,'published':date,'source':s['name'],'category':'stock'})
   break
  except Exception: continue
seen=set(); clean=[]
for n in items:
 k=(n['url'] or n['title']).lower()
 if n['title'] and k not in seen:seen.add(k);clean.append(n)
OUT.parent.mkdir(exist_ok=True);OUT.write_text(json.dumps(clean[:500],ensure_ascii=False,indent=2))
print('Collected',len(clean),'news items')
