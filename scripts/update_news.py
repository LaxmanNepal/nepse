#!/usr/bin/env python3
"""Build a Nepali-only, NEPSE-focused news feed from public Google News RSS search results."""
from __future__ import annotations
import html
import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/news.json"
QUERIES = [
    '"नेप्से" OR "शेयर बजार" OR "सेयर बजार" site:merolagani.com',
    '"नेप्से" OR "शेयर बजार" OR "सेयर बजार" site:sharesansar.com',
    '"आईपीओ" OR "लाभांश" OR "हकप्रद" OR "बोनस शेयर" Nepal share market',
    '"नेप्से" OR "सूचीकृत कम्पनी" OR "शेयर कारोबार" site:arthasarokar.com',
]
MARKET_TERMS = ("नेप्से", "शेयर", "सेयर", "आईपीओ", "आइपिओ", "लाभांश", "हकप्रद", "बोनस शेयर", "साधारणसभा", "सूचीकृत कम्पनी", "कारोबार", "ब्रोकर", "धितोपत्र", "merolagani", "sharesansar", "nepse")
IPO_TERMS = ("आईपीओ", "आइपिओ", "हकप्रद", "एफपीओ", "बुक बिल्डिङ")
DIVIDEND_TERMS = ("लाभांश", "बोनस शेयर", "बोनस सेयर", "बुक क्लोज")
COMPANY_TERMS = ("कम्पनी", "बैंक", "हाइड्रो", "लघुवित्त", "बीमा", "वित्त", "सूचीकृत", "साधारणसभा", "नाफा", "वित्तीय")
def clean(value: str) -> str:
    value = html.unescape(re.sub(r"<[^>]+>", " ", value or ""))
    return re.sub(r"\\s+", " ", value).strip()
def category(title: str) -> tuple[str, str]:
    t = title.lower()
    if any(k in t for k in IPO_TERMS): return "ipo", "आईपीओ / हकप्रद"
    if any(k in t for k in DIVIDEND_TERMS): return "dividend", "लाभांश / बोनस"
    if any(k in t for k in COMPANY_TERMS): return "company", "कम्पनी समाचार"
    return "market", "नेप्से / बजार"
def is_nepali_market_item(title: str) -> bool:
    if not re.search(r"[\\u0900-\\u097F]", title): return False
    t = title.lower()
    return any(k in t for k in MARKET_TERMS)
def fetch_query(query: str) -> list[dict]:
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode({"q": query, "hl": "ne", "gl": "NP", "ceid": "NP:ne"})
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 NEPSE-Terminal-News/1.0"})
    with urllib.request.urlopen(req, timeout=25) as response:
        root = ET.fromstring(response.read())
    items = []
    for item in root.findall("./channel/item"):
        title = clean(item.findtext("title", ""))
        if not is_nepali_market_item(title): continue
        source_el = item.find("source")
        source = clean(source_el.text if source_el is not None else "समाचार स्रोत")
        link = clean(item.findtext("link", ""))
        if not link.startswith("https://"): continue
        summary = clean(item.findtext("description", ""))
        published = clean(item.findtext("pubDate", ""))
        cat, label = category(title)
        items.append({"title": title, "summary": summary[:500], "url": link, "source": source, "published": published, "category": cat, "categoryLabel": label, "symbols": []})
    return items
def main() -> None:
    gathered = []
    for query in QUERIES:
        try: gathered.extend(fetch_query(query))
        except Exception as exc: print(f"RSS query failed: {exc}")
        time.sleep(1)
    unique = {}
    for item in gathered:
        key = re.sub(r"[^\\w\\u0900-\\u097F]", "", item["title"].lower())
        if key and key not in unique: unique[key] = item
    items = sorted(unique.values(), key=lambda x: x.get("published", ""), reverse=True)[:80]
    if not items and OUT.exists():
        previous = json.loads(OUT.read_text(encoding="utf-8"))
        age = (datetime.now(timezone.utc) - datetime.fromisoformat(previous["updatedAt"].replace("Z", "+00:00"))).total_seconds()
        if age < 86400:
            print("No new RSS items; preserving last feed snapshot.")
            return
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"schemaVersion": 1, "updatedAt": datetime.now(timezone.utc).isoformat(), "language": "Nepali headlines only", "scope": "NEPSE and listed-company news", "items": items}, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
    print(f"Wrote {len(items)} NEPSE-related Nepali news items.")
if __name__ == "__main__": main()
