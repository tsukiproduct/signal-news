#!/usr/bin/env python3
"""
AI News Fetcher — Phase 1 (Python固定ロジック)
役割: RSSを取得してraw JSONに変換する。判断・スコアリングは一切しない。
実行: python3 fetch_news.py
出力: ../docs/data/raw.json  （curate.py が次に処理する）
"""

import json
import re
import time
import hashlib
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError

# ─── RSS ソース定義 ─────────────────────────────────────────────────────────
# priority: 1=最高優先（Featured候補）, 2=標準, 3=補完
FEEDS = [

    # ── 研究・一次情報（EN）
    {"url": "https://openai.com/blog/rss.xml",
     "source": "OpenAI Blog",        "lang": "en", "category": "Research", "priority": 1},
    {"url": "https://deepmind.google/blog/rss.xml",
     "source": "Google DeepMind",    "lang": "en", "category": "Research", "priority": 1},
    {"url": "https://bair.berkeley.edu/blog/feed.xml",
     "source": "BAIR Blog",          "lang": "en", "category": "Research", "priority": 1},
    {"url": "https://thegradient.pub/rss/",
     "source": "The Gradient",       "lang": "en", "category": "Research", "priority": 1},
    {"url": "https://newsletter.importai.net/feed",
     "source": "Import AI",          "lang": "en", "category": "Research", "priority": 1},
    {"url": "https://paperswithcode.com/rss.xml",
     "source": "Papers With Code",   "lang": "en", "category": "Research", "priority": 2},
    {"url": "https://www.alignmentforum.org/feed.xml",
     "source": "Alignment Forum",    "lang": "en", "category": "Safety",   "priority": 2},

    # ── ビジネス・産業（EN）
    {"url": "https://venturebeat.com/category/ai/feed/",
     "source": "VentureBeat AI",     "lang": "en", "category": "Industry", "priority": 1},
    {"url": "https://techcrunch.com/category/artificial-intelligence/feed/",
     "source": "TechCrunch AI",      "lang": "en", "category": "Industry", "priority": 1},
    {"url": "https://www.technologyreview.com/feed/",
     "source": "MIT Tech Review",    "lang": "en", "category": "Research", "priority": 1},
    {"url": "https://www.theverge.com/rss/index.xml",
     "source": "The Verge",          "lang": "en", "category": "Tech",     "priority": 2},
    {"url": "https://feeds.arstechnica.com/arstechnica/technology-lab",
     "source": "Ars Technica",       "lang": "en", "category": "Tech",     "priority": 2},
    {"url": "https://feeds.bloomberg.com/technology/news.rss",
     "source": "Bloomberg Tech",     "lang": "en", "category": "Industry", "priority": 2},
    {"url": "https://feeds.reuters.com/reuters/technologyNews",
     "source": "Reuters Tech",       "lang": "en", "category": "Industry", "priority": 2},
    {"url": "https://feeds.feedburner.com/oreilly/radar",
     "source": "O'Reilly Radar",     "lang": "en", "category": "Tech",     "priority": 2},
    {"url": "https://lastweekin.ai/feed",
     "source": "Last Week in AI",    "lang": "en", "category": "Research", "priority": 2},
    {"url": "https://www.aisnakeoil.com/feed",
     "source": "AI Snake Oil",       "lang": "en", "category": "Safety",   "priority": 2},
    {"url": "https://chinaaiwkly.substack.com/feed",
     "source": "China AI Weekly",    "lang": "en", "category": "Industry", "priority": 2},

    # ── 日本語（国内）
    {"url": "https://ledge.ai/feed/",
     "source": "Ledge.ai",           "lang": "ja", "category": "AI",       "priority": 1},
    {"url": "https://ainow.ai/feed/",
     "source": "AINOW",              "lang": "ja", "category": "AI",       "priority": 1},
    {"url": "https://www.itmedia.co.jp/rss/2.0/aiplus.rdf",
     "source": "ITmedia AI+",        "lang": "ja", "category": "Tech",     "priority": 1},
    {"url": "https://gigazine.net/news/rss_2.0/",
     "source": "Gigazine",           "lang": "ja", "category": "Tech",     "priority": 2},
    {"url": "https://ascii.jp/rss.xml",
     "source": "ASCII.jp",           "lang": "ja", "category": "Tech",     "priority": 2},
    {"url": "https://news.mynavi.jp/rss/tech",
     "source": "マイナビニュース",     "lang": "ja", "category": "Tech",     "priority": 2},
    {"url": "https://www.nhk.or.jp/rss/news/cat5.xml",
     "source": "NHK テクノロジー",    "lang": "ja", "category": "Society",  "priority": 2},
    {"url": "https://www.meti.go.jp/rss/press.rdf",
     "source": "経済産業省",           "lang": "ja", "category": "Policy",   "priority": 1},
    {"url": "https://www.denkei.co.jp/rss.xml",
     "source": "電経新聞",             "lang": "ja", "category": "Industry", "priority": 3},
]

RAW_PATH           = Path(__file__).parent.parent / "docs" / "data" / "raw.json"
MAX_ITEMS_PER_FEED = 8
MAX_TOTAL_ITEMS    = 200
TIMEOUT            = 12

NAMESPACES = {
    "media": "http://search.yahoo.com/mrss/",
    "dc":    "http://purl.org/dc/elements/1.1/",
}
ATOM_NS = "http://www.w3.org/2005/Atom"


def make_id(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:12]


def strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    for ent, ch in [("&amp;","&"),("&lt;","<"),("&gt;",">"),("&quot;",'"'),("&#39;","'")]:
        text = text.replace(ent, ch)
    return re.sub(r"\s+", " ", text).strip()


def parse_date(raw: str) -> str:
    for fmt in ["%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S GMT",
                "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S"]:
        try:
            dt = datetime.strptime(raw.strip(), fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).isoformat()
        except ValueError:
            continue
    return datetime.now(timezone.utc).isoformat()


def fetch_feed(meta: dict) -> list:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; SIGNALNewsBot/2.0)",
        "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml",
    }
    try:
        req = Request(meta["url"], headers=headers)
        with urlopen(req, timeout=TIMEOUT) as resp:
            raw = resp.read()
        root = ET.fromstring(raw)
    except Exception as e:
        print(f"  ✗ {meta['source']}: {e}")
        return []

    items, seen_links = [], set()

    def add(title, link, summary, date_raw):
        title = strip_html(title).strip()
        link  = link.strip()
        if not title or not link or link in seen_links:
            return
        seen_links.add(link)
        items.append({
            "id":       make_id(link),
            "title":    title,
            "url":      link,
            "summary":  strip_html(summary)[:250],
            "date":     parse_date(date_raw),
            "source":   meta["source"],
            "lang":     meta["lang"],
            "category": meta["category"],
            "priority": meta["priority"],
        })

    for item in root.findall(".//item")[:MAX_ITEMS_PER_FEED]:
        add(item.findtext("title",""), item.findtext("link",""),
            item.findtext("description",""),
            item.findtext("pubDate") or item.findtext("dc:date", namespaces=NAMESPACES) or "")

    for entry in root.findall(f".//{{{ATOM_NS}}}entry")[:MAX_ITEMS_PER_FEED]:
        lk = entry.find(f"{{{ATOM_NS}}}link")
        add(entry.findtext(f"{{{ATOM_NS}}}title",""),
            lk.get("href","") if lk is not None else "",
            entry.findtext(f"{{{ATOM_NS}}}summary","") or entry.findtext(f"{{{ATOM_NS}}}content",""),
            entry.findtext(f"{{{ATOM_NS}}}updated") or entry.findtext(f"{{{ATOM_NS}}}published") or "")

    print(f"  ✓ {meta['source']}: {len(items)} items")
    return items


def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Phase 1: Fetching {len(FEEDS)} RSS feeds...")
    all_items, seen_ids = [], set()

    for meta in FEEDS:
        for item in fetch_feed(meta):
            if item["id"] not in seen_ids:
                seen_ids.add(item["id"])
                all_items.append(item)
        time.sleep(0.4)

    all_items.sort(key=lambda x: x["date"], reverse=True)
    all_items = all_items[:MAX_TOTAL_ITEMS]

    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    RAW_PATH.write_text(json.dumps({
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "total": len(all_items),
        "items": all_items,
    }, ensure_ascii=False, indent=2))
    print(f"\n✅ Phase 1 done — {len(all_items)} raw items → {RAW_PATH}")


if __name__ == "__main__":
    main()
