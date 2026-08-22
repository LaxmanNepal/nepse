import json, pathlib, re, urllib.request, xml.etree.ElementTree as ET
from html.parser import HTMLParser
ROOT=pathlib.Path(__file__).resolve().parents[1]; REG=ROOT/'data/news-sources.json'; OUT=ROOT/'data/news.json'
UA='Mozilla/5.0 (compatible; NEPSE-Pulse/1.0)'
def get(url):
 r=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'application/rss+xml,application/atom+xml,application/xml,text/html'}); return urllib.request.urlopen(r,timeout=20).read()
def clean(x): return re.sub(r'\s+',' ',x or '').strip()
class Links(HTMLParser):
 def __init__(self): super().__init__(); self.href=''; self.buf=''; self.rows=[]
 def handle_starttag(self,t,a):
  if t=='a': self.href=dict(a).get('href',''); self.buf=''
 def handle_data(self,d): self.buf+=d
 def handle_endtag(self,t):
  if t=='a' and self.href and clean(self.buf): self.rows.append((clean(self.buf),self.href)); self.href=''; self.buf=''
def category(title):
 b=title.lower()
 if any(k in b for k in ('ipo','fpo','auction','right share','आइपिओ','एफपिओ')): return 'ipo'
 if any(k in b for k in ('dividend','bonus','लाभांश','बोनस')): return 'dividend'
 if any(k in b for k in ('nepse','share','stock','शेयर','सेयर','बजार')): return 'stock'
 if any(k in b for k in ('bank','insurance','hydro','microfinance','बैंक','बीमा','हाइड्रो')): return 'company'
 if any(k in b for k in ('economy','अर्थतन्त्र','अर्थव्यवस्था')): return 'economy'
 return 'finance'
def xml_items(raw,source):
 root=ET.fromstring(raw); ns={'a':'http://www.w3.org/2005/Atom'}; entries=root.findall('.//item') or root.findall('.//a:entry',ns); out=[]
 for e in entries[:200]:
  title=clean((e.findtext('title') or e.findtext('a:title',default='',namespaces=ns))); link=e.findtext('link') or ''
  if not link:
   le=e.find('a:link',ns); link=le.attrib.get('href','') if le is not None else ''
  date=clean(e.findtext('pubDate') or e.findtext('a:updated',default='',namespaces=ns))
  if title and link: out.append({'title':title,'url':link,'published':date,'source':source,'category':category(title)})
 return out
def html_items(raw,source,base):
 p=Links(); p.feed(raw.decode('utf-8','ignore')); out=[]
 for title,link in p.rows:
  if len(title)<15 or len(title)>240: continue
  if link.startswith('/'): link=base.rstrip('/')+link
  if not link.startswith('http'): continue
  out.append({'title':title,'url':link,'published':'','source':source,'category':category(title)})
 return out
def main():
 cfg=json.loads(REG.read_text()); merged={}
 if OUT.exists():
  try: merged={x['url']:x for x in json.loads(OUT.read_text()) if x.get('url')}
  except Exception: pass
 for s in cfg['sources']:
  urls=[s.get(k) for k in ('feed','rss','atom','news','announcements') if s.get(k)]
  for u in urls:
   try:
    raw=get(u)
    try: found=xml_items(raw,s['name'])
    except Exception: found=html_items(raw,s['name'],s.get('url',''))
    for x in found: merged[x['url']]=x
   except Exception as e: print('skip',s['name'],u,e)
 data=sorted(merged.values(),key=lambda x:x.get('published',''),reverse=True)[:1000]
 OUT.parent.mkdir(exist_ok=True); OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2))
 print('Collected',len(data),'news items')
if __name__=='__main__': main()
