#!/usr/bin/env python3
"""Build a Nepali-only NEPSE news feed and capture publisher article thumbnails."""
from __future__ import annotations
import html, json, re, time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/news.json"
QUERIES = [
    '"नेप्से" when:14d', '"शेयर बजार" when:14d', '"सेयर बजार" when:14d',
    '"आईपीओ" OR "लाभांश" OR "हकप्रद" when:14d',
    'site:nepseanalysis.com "नेप्से" when:14d',
    'site:merolagani.com "नेप्से" when:14d',
    'site:sharesansar.com "नेप्से" when:14d',
    'site:equitynepal.com "नेप्से" when:14d',
    'site:arthakhabar.com "नेप्से" when:14d',
]
MARKET_TERMS = ("नेप्से", "शेयर", "सेयर", "आईपीओ", "आइपिओ", "लाभांश", "हकप्रद", "बोनस शेयर", "साधारणसभा", "सूचीकृत कम्पनी", "कारोबार", "ब्रोकर", "धितोपत्र")
NEPAL_MARKET_TERMS = ("नेप्से", "नेपाल", "नेपाली", "nepse", "nepal")
NEPAL_SOURCES = ("merolagani", "sharesansar", "artha sarokar", "arthasarokar", "arthasansar", "nepali paisa", "nepalipaisa", "bizmandu", "capital nepal", "nepse analysis", "nepseanalysis", "lagani saathi", "nepse trading", "nepsealpha", "equitynepal", "artha khabar", "arthakhabar")
IPO_TERMS = ("आईपीओ", "आइपिओ", "हकप्रद", "एफपीओ", "बुक बिल्डिङ")
DIVIDEND_TERMS = ("लाभांश", "बोनस शेयर", "बोनस सेयर", "बुक क्लोज")
COMPANY_TERMS = ("कम्पनी", "बैंक", "हाइड्रो", "लघुवित्त", "बीमा", "वित्त", "सूचीकृत", "साधारणसभा", "नाफा", "वित्तीय")

def clean(value: str) -> str:
    value = html.unescape(re.sub(r"<[^>]+>", " ", value or ""))
    return re.sub(r"\s+", " ", value).strip()

def category(title: str) -> tuple[str, str]:
    t = title.lower()
    if any(k in t for k in IPO_TERMS): return "ipo", "आईपीओ / हकप्रद"
    if any(k in t for k in DIVIDEND_TERMS): return "dividend", "लाभांश / बोनस"
    if any(k in t for k in COMPANY_TERMS): return "company", "कम्पनी समाचार"
    return "market", "नेप्से / बजार"

def is_nepali_market_item(title: str, source: str = "") -> bool:
    if not re.search(r"[\u0900-\u097F]", title): return False
    t, src = title.lower(), source.lower()
    if not any(k in t for k in MARKET_TERMS): return False
    return any(k in t for k in NEPAL_MARKET_TERMS) or any(k in src for k in NEPAL_SOURCES)

class ImageMetaParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.images = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag.lower() == "meta":
            key = (a.get("property") or a.get("name") or "").lower()
            if key in ("og:image", "og:image:url", "twitter:image", "twitter:image:src"):
                self.images.append(a.get("content", ""))
        elif tag.lower() == "link" and "image_src" in (a.get("rel") or "").lower():
            self.images.append(a.get("href", ""))

def valid_image(candidate: str, base: str) -> str:
    candidate = html.unescape((candidate or "").strip())
    if not candidate or candidate.startswith("data:"): return ""
    url = urllib.parse.urljoin(base, candidate)
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc: return ""
    if any(x in parsed.netloc.lower() for x in ("google.com", "gstatic.com")): return ""
    return url

def article_image(url: str, rss_image: str = "") -> str:
    found = valid_image(rss_image, url)
    if found: return found
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; NEPSE-NewsBot/1.0)", "Accept": "text/html"})
        with urllib.request.urlopen(req, timeout=8) as response:
            if "html" not in response.headers.get("Content-Type", "").lower(): return ""
            page = response.read(350_000).decode("utf-8", errors="ignore")
            parser = ImageMetaParser(); parser.feed(page)
            for candidate in parser.images:
                found = valid_image(candidate, response.geturl())
                if found: return found
    except Exception as exc:
        print(f"Image lookup skipped for {url}: {exc}")
    return ""

def fetch_query(query: str) -> list[dict]:
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode({"q": query, "hl": "ne", "gl": "NP", "ceid": "NP:ne"})
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 NEPSE-Terminal-News/1.0"})
    with urllib.request.urlopen(req, timeout=25) as response:
        root = ET.fromstring(response.read())
    items = []
    for item in root.findall("./channel/item"):
        title = clean(item.findtext("title", ""))
        source_el = item.find("source")
        source = clean(source_el.text if source_el is not None else "समाचार स्रोत")
        if not is_nepali_market_item(title, source): continue
        link = clean(item.findtext("link", ""))
        if not link.startswith("https://"): continue
        summary = clean(item.findtext("description", ""))
        if not re.search(r"[\u0900-\u097F]", summary): summary = ""
        published = clean(item.findtext("pubDate", ""))
        try:
            published_dt = parsedate_to_datetime(published)
            if published_dt.tzinfo is None: published_dt = published_dt.replace(tzinfo=timezone.utc)
            if (datetime.now(timezone.utc) - published_dt.astimezone(timezone.utc)).total_seconds() > 14 * 86400: continue
        except (TypeError, ValueError, OverflowError): continue
        media = "{http://search.yahoo.com/mrss/}thumbnail"
        media_content = "{http://search.yahoo.com/mrss/}content"
        image = ""
        node = item.find(media)
        if node is not None: image = node.attrib.get("url", "")
        if not image:
            node = item.find(media_content)
            if node is not None and node.attrib.get("medium") == "image": image = node.attrib.get("url", "")
        if not image:
            enclosure = item.find("enclosure")
            if enclosure is not None and enclosure.attrib.get("type", "").startswith("image/"): image = enclosure.attrib.get("url", "")
        if not image:
            match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', item.findtext("description", "") or "", re.I)
            if match: image = match.group(1)
        cat, label = category(title)
        items.append({"title": title, "summary": summary[:500], "url": link, "source": source, "published": published, "category": cat, "categoryLabel": label, "symbols": [], "imageUrl": valid_image(image, link)})
    return items

def main() -> None:
    gathered = []
    for query in QUERIES:
        try: gathered.extend(fetch_query(query))
        except Exception as exc: print(f"RSS query failed: {exc}")
        time.sleep(1)
    unique = {}
    for item in gathered:
        key = re.sub(r"[^\w\u0900-\u097F]", "", item["title"].lower())
        if key and key not in unique: unique[key] = item
    items = sorted(unique.values(), key=lambda x: x.get("published", ""), reverse=True)[:80]
    if not items and OUT.exists():
        try:
            previous = json.loads(OUT.read_text(encoding="utf-8"))
            cutoff = datetime.now(timezone.utc).timestamp() - 14 * 86400
            items = [x for x in previous.get("items", []) if parsedate_to_datetime(x.get("published", "")).timestamp() >= cutoff]
        except (OSError, ValueError, TypeError, KeyError):
            items = []
    previous_by_url = {}
    if OUT.exists():
        try: previous_by_url = {x.get("url"): x for x in json.loads(OUT.read_text(encoding="utf-8")).get("items", [])}
        except Exception: pass
    # Preserve cached thumbnails; resolve publisher OG images for a bounded batch each run.
    for item in items:
        old = previous_by_url.get(item["url"], {})
        if not item.get("imageUrl"): item["imageUrl"] = old.get("imageUrl", "")
    needs_image = [x for x in items if not x.get("imageUrl")][:30]
    for item in needs_image:
        item["imageUrl"] = article_image(item["url"], item.get("imageUrl", ""))
        time.sleep(0.35)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"schemaVersion": 1, "updatedAt": datetime.now(timezone.utc).isoformat(), "language": "Nepali headlines only", "scope": "NEPSE and listed-company news", "items": items}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(items)} NEPSE-related Nepali news items; {sum(bool(x.get('imageUrl')) for x in items)} have thumbnails.")

if __name__ == "__main__": main()
