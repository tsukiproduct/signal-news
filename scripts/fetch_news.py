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
# category: AI / Research / Industry / Tech / Safety / Policy / JP / EN
#           Wow / Events / Prompts / ImageVideo  ← NEW
FEEDS = [

    # ══════════════════════════════════════════
    # 既存ソース（変更なし）
    # ══════════════════════════════════════════

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
     "source": "NHK テクノロジー",    "lang": "ja", "category": "AI",      "priority": 2},
    {"url": "https://www.meti.go.jp/rss/press.rdf",
     "source": "経済産業省",           "lang": "ja", "category": "Policy",   "priority": 1},
    {"url": "https://www.denkei.co.jp/rss.xml",
     "source": "電経新聞",             "lang": "ja", "category": "Industry", "priority": 3},

    # ══════════════════════════════════════════
    # NEW: Prompts カテゴリ
    # プロンプト・AI活用ノウハウ系（RSS・無料・無登録）
    # ══════════════════════════════════════════
    {"url": "https://simonwillison.net/atom/everything/",
     "source": "Simon Willison",     "lang": "en", "category": "Prompts",  "priority": 1},
    {"url": "https://huggingface.co/blog/feed.xml",
     "source": "Hugging Face Blog",  "lang": "en", "category": "Prompts",  "priority": 1},
    {"url": "https://www.promptingguide.ai/feed.xml",
     "source": "Prompt Guide",       "lang": "en", "category": "Prompts",  "priority": 2},
    {"url": "https://learnprompting.org/feed.xml",
     "source": "Learn Prompting",    "lang": "en", "category": "Prompts",  "priority": 2},

    # ══════════════════════════════════════════
    # NEW: ImageVideo カテゴリ
    # 画像・動画生成AI系（RSS・無料・無登録）
    # ══════════════════════════════════════════
    {"url": "https://stability.ai/news/rss.xml",
     "source": "Stability AI",       "lang": "en", "category": "ImageVideo","priority": 1},
    {"url": "https://blog.research.google/feeds/posts/default/-/generative-ai",
     "source": "Google AI Blog",     "lang": "en", "category": "ImageVideo","priority": 1},
    {"url": "https://www.reddit.com/r/StableDiffusion/.rss",
     "source": "r/StableDiffusion",  "lang": "en", "category": "ImageVideo","priority": 2},
    {"url": "https://www.reddit.com/r/MediaSynthesis/.rss",
     "source": "r/MediaSynthesis",   "lang": "en", "category": "ImageVideo","priority": 2},

    # ══════════════════════════════════════════
    # NEW: Wow カテゴリ
    # バイラル・驚き系AI情報（HN + Reddit・無料・無登録）
    # ══════════════════════════════════════════
    {"url": "https://www.reddit.com/r/artificial/.rss",
     "source": "r/artificial",       "lang": "en", "category": "Wow",      "priority": 2},
    {"url": "https://www.reddit.com/r/MachineLearning/.rss",
     "source": "r/MachineLearning",  "lang": "en", "category": "Wow",      "priority": 2},
]

RAW_PATH           = Path(__file__).parent.parent / "docs" / "data" / "raw.json"
MAX_ITEMS_PER_FEED = 8
MAX_TOTAL_ITEMS    = 250   # 新カテゴリ追加分を考慮して200→250に拡張
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


# ══════════════════════════════════════════
# NEW: HackerNews Algolia API（Wowカテゴリ補完）
# 公式API・無料・無登録
# ══════════════════════════════════════════
def fetch_hackernews(limit: int = 10) -> list:
    """HN Algolia APIからAI関連トップ記事を取得"""
    url = (
        "https://hn.algolia.com/api/v1/search"
        "?query=AI+machine+learning"
        "&tags=story"
        "&numericFilters=points>50"
        f"&hitsPerPage={limit}"
    )
    try:
        req = Request(url, headers={"User-Agent": "SIGNALNewsBot/2.0"})
        with urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read())

        items = []
        for hit in data.get("hits", []):
            link = hit.get("url") or f"https://news.ycombinator.com/item?id={hit['objectID']}"
            title = strip_html(hit.get("title", "")).strip()
            if not title or not link:
                continue
            # 投稿日時
            created = hit.get("created_at", "")
            items.append({
                "id":       make_id(link),
                "title":    title,
                "url":      link,
                "summary":  f"▲ {hit.get('points',0)} points · {hit.get('num_comments',0)} comments on HackerNews",
                "date":     parse_date(created) if created else datetime.now(timezone.utc).isoformat(),
                "source":   "HackerNews",
                "lang":     "en",
                "category": "Wow",
                "priority": 1,
            })
        print(f"  ✓ HackerNews: {len(items)} items")
        return items
    except Exception as e:
        print(f"  ✗ HackerNews: {e}")
        return []


# ══════════════════════════════════════════
# NEW: connpass API（Eventsカテゴリ）
# 公式API・無料・無登録
# ══════════════════════════════════════════
def fetch_connpass(limit: int = 10) -> list:
    """connpass公式APIからAI関連イベントを取得"""
    url = (
        "https://connpass.com/api/v1/event/"
        "?keyword=AI,機械学習,人工知能,LLM,ChatGPT"
        "&order=2"      # 開催日順
        f"&count={limit}"
    )
    try:
        req = Request(url, headers={"User-Agent": "SIGNALNewsBot/2.0"})
        with urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read())

        items = []
        for ev in data.get("events", []):
            link  = ev.get("event_url", "")
            title = ev.get("title", "").strip()
            if not title or not link:
                continue

            place    = ev.get("place") or ev.get("address") or "オンライン"
            started  = ev.get("started_at", "")
            accepted = ev.get("accepted", 0)
            limit_n  = ev.get("limit", "")
            limit_str = f"/{limit_n}" if limit_n else ""

            summary = (
                f"📅 {started[:10] if started else '日程未定'} · "
                f"📍 {place[:30]} · "
                f"👥 参加 {accepted}{limit_str}人"
            )
            items.append({
                "id":       make_id(link),
                "title":    title,
                "url":      link,
                "summary":  summary,
                "date":     parse_date(started) if started else datetime.now(timezone.utc).isoformat(),
                "source":   "connpass",
                "lang":     "ja",
                "category": "Events",
                "priority": 1,
                # イベント専用フィールド
                "event_date":  started[:10] if started else "",
                "event_place": place,
                "event_online": not bool(ev.get("address")),
            })
        print(f"  ✓ connpass: {len(items)} items")
        return items
    except Exception as e:
        print(f"  ✗ connpass: {e}")
        return []


# ══════════════════════════════════════════
# NEW: Doorkeeper API（Eventsカテゴリ補完）
# 公式JSON API・無料・無登録
# ══════════════════════════════════════════
def fetch_doorkeeper(limit: int = 8) -> list:
    """Doorkeeper公式APIからAI関連イベントを取得"""
    url = f"https://api.doorkeeper.jp/events?q=AI&per_page={limit}"
    try:
        req = Request(url, headers={
            "User-Agent": "SIGNALNewsBot/2.0",
            "Accept": "application/json",
        })
        with urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read())

        items = []
        for ev in data:
            ev = ev.get("event", ev)  # ネスト構造に対応
            link  = ev.get("public_url", "")
            title = ev.get("title", "").strip()
            if not title or not link:
                continue

            starts = ev.get("starts_at", "")
            venue  = ev.get("venue_name") or "オンライン"
            ticket_limit = ev.get("ticket_limit", "")
            participants = ev.get("participants", 0)
            limit_str = f"/{ticket_limit}" if ticket_limit else ""

            summary = (
                f"📅 {starts[:10] if starts else '日程未定'} · "
                f"📍 {venue[:30]} · "
                f"👥 参加 {participants}{limit_str}人"
            )
            items.append({
                "id":       make_id(link),
                "title":    title,
                "url":      link,
                "summary":  summary,
                "date":     parse_date(starts) if starts else datetime.now(timezone.utc).isoformat(),
                "source":   "Doorkeeper",
                "lang":     "ja",
                "category": "Events",
                "priority": 2,
                "event_date":   starts[:10] if starts else "",
                "event_place":  venue,
                "event_online": ev.get("location_type") == "online",
            })
        print(f"  ✓ Doorkeeper: {len(items)} items")
        return items
    except Exception as e:
        print(f"  ✗ Doorkeeper: {e}")
        return []


def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Phase 1: Fetching {len(FEEDS)} RSS feeds + APIs...")
    all_items, seen_ids = [], set()

    # ── RSS feeds ─────────────────────────────────────────────────────────
    for meta in FEEDS:
        for item in fetch_feed(meta):
            if item["id"] not in seen_ids:
                seen_ids.add(item["id"])
                all_items.append(item)
        time.sleep(0.4)

    # ── HackerNews（Wow） ─────────────────────────────────────────────────
    for item in fetch_hackernews(limit=15):
        if item["id"] not in seen_ids:
            seen_ids.add(item["id"])
            all_items.append(item)

    # ── connpass（Events） ────────────────────────────────────────────────
    for item in fetch_connpass(limit=15):
        if item["id"] not in seen_ids:
            seen_ids.add(item["id"])
            all_items.append(item)

    # ── Doorkeeper（Events補完） ──────────────────────────────────────────
    for item in fetch_doorkeeper(limit=10):
        if item["id"] not in seen_ids:
            seen_ids.add(item["id"])
            all_items.append(item)

    # ── 並び替え・件数制限 ─────────────────────────────────────────────────
    # Eventsは開催日順（近い順）、それ以外は取得日時降順
    events = sorted(
        [x for x in all_items if x["category"] == "Events"],
        key=lambda x: x["date"]
    )
    others = sorted(
        [x for x in all_items if x["category"] != "Events"],
        key=lambda x: x["date"], reverse=True
    )
    all_items = others[:MAX_TOTAL_ITEMS] + events

    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    RAW_PATH.write_text(json.dumps({
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "total": len(all_items),
        "items": all_items,
    }, ensure_ascii=False, indent=2))
    print(f"\n✅ Phase 1 done — {len(all_items)} raw items → {RAW_PATH}")

    # カテゴリ別件数ログ
    from collections import Counter
    dist = Counter(x["category"] for x in all_items)
    print("  Category breakdown:", dict(sorted(dist.items())))


if __name__ == "__main__":
    main()
