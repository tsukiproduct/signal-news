#!/usr/bin/env python3
"""
SIGNAL Digest Generator — Phase 2.5
OpenRouter API（無料モデル）使用版

無料モデル: meta-llama/llama-3.1-8b-instruct:free
新カテゴリ（Wow / Events / Prompts / ImageVideo）をdigestに反映
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from pathlib import Path

NEWS_PATH    = Path(__file__).parent.parent / "docs" / "data" / "news.json"
ARTICLES_DIR = Path(__file__).parent.parent / "docs" / "articles"
DIGESTS_PATH = Path(__file__).parent.parent / "docs" / "data" / "digests.json"

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL      = "openrouter/free"
MAX_TOKENS = 3000
TEMPERATURE = 0.7

TOP_ARTICLES   = 5
MAX_DIGESTS    = 30
TOP_WOW        = 2   # Wowカテゴリから何件digestに含めるか
TOP_PROMPTS    = 1   # Promptsカテゴリから何件digestに含めるか
TOP_EVENTS     = 2   # Eventsカテゴリから何件digestに含めるか
TOP_IMAGEVIDEO = 1   # ImageVideoカテゴリから何件digestに含めるか

SYSTEM_PROMPT = """あなたはAI技術の専門ジャーナリストです。
提供されたAIニュースをもとに、読者に役立つオリジナル解説記事を日本語で書いてください。

ルール:
- 元記事の文章をそのまま転載しない
- タイトルとURLは出典として明示する
- 解説・考察・応用は自分の言葉で書く
- 事実と考察を明確に区別する
- 誇大な表現を避ける
- 画像・動画生成AIや注目プロンプト、イベント情報も積極的に取り上げる

出力はJSONのみ。前置き不要。"""

USER_PROMPT_TEMPLATE = """{count}本のAIニュース・情報をもとに解説記事を生成してください。

【参照ニュース・情報】
{news_list}

【出力JSON】
{{
  "title": "記事タイトル（40字以内）",
  "slug": "english-slug",
  "summary": "要約（80字以内）",
  "sections": [
    {{
      "type": "overview",
      "heading": "今日のAI概観",
      "body": "導入文（200字程度）"
    }},
    {{
      "type": "deep_dive",
      "heading": "注目トピック詳説",
      "body": "背景・意味・影響を解説（400字程度）",
      "source_title": "参照記事タイトル",
      "source_url": "参照記事URL"
    }},
    {{
      "type": "imagevideo",
      "heading": "画像・動画生成AIの最前線",
      "body": "画像・動画生成AI関連の注目情報（200字程度）。該当情報がなければ省略可。",
      "source_title": "参照記事タイトル（任意）",
      "source_url": "参照記事URL（任意）"
    }},
    {{
      "type": "prompt_of_day",
      "heading": "今日のプロンプト",
      "prompt_title": "プロンプトタイトル（20字以内）",
      "prompt_body": "実用的なプロンプト（150字程度）",
      "prompt_usecase": "使い方（100字程度）",
      "prompt_source": "参照記事URL（任意）"
    }},
    {{
      "type": "wow",
      "heading": "これはすごい！今週のバイラル",
      "body": "HackerNews・Redditで話題のAI情報（200字程度）。該当情報がなければ省略可。",
      "source_title": "参照記事タイトル（任意）",
      "source_url": "参照記事URL（任意）"
    }},
    {{
      "type": "events",
      "heading": "今週のAIイベント",
      "body": "注目のオンライン・オフラインイベント情報（200字程度）。該当情報がなければ省略可。",
      "event_list": [
        {{"title": "イベント名", "date": "日程", "place": "会場/オンライン", "url": "URL"}}
      ]
    }},
    {{
      "type": "practical",
      "heading": "実践：ビジネスへの応用",
      "body": "具体的な活用方法（300字程度）"
    }},
    {{
      "type": "weekly_watch",
      "heading": "今週注目すべきこと",
      "body": "トレンド・展望（200字程度）"
    }}
  ],
  "tags": ["タグ1", "タグ2", "タグ3"],
  "affiliate_context": "AI入門書"
}}"""

AFFILIATE_MAP = {
    "AI入門書": {
        "label": "AIを学ぶための入門書セレクション",
        "url": "https://www.amazon.co.jp/s?k=人工知能+機械学習+入門&tag=tsukiproduct-22",
        "cta": "Amazon で探す →",
    },
    "機械学習コース": {
        "label": "Udemy AI・機械学習コース（セール中）",
        "url": "https://www.udemy.com/courses/search/?q=機械学習+AI&sort=popularity&lang=ja",
        "cta": "コースを見る →",
    },
    "クラウドGPU": {
        "label": "GPU クラウド環境を無料で試す",
        "url": "https://colab.research.google.com/",
        "cta": "Google Colab を試す →",
    },
    "プロンプト本": {
        "label": "プロンプトエンジニアリング実践ガイド",
        "url": "https://www.amazon.co.jp/s?k=プロンプトエンジニアリング&tag=tsukiproduct-22",
        "cta": "Amazon で探す →",
    },
    "画像生成AI本": {
        "label": "画像生成AI活用ガイド（Stable Diffusion・Midjourney）",
        "url": "https://www.amazon.co.jp/s?k=画像生成AI+Stable+Diffusion&tag=tsukiproduct-22",
        "cta": "Amazon で探す →",
    },
}
DEFAULT_AFFILIATE = "機械学習コース"


def pick_top_items(items: list) -> list:
    """
    カテゴリ別に上位記事を選出してdigest用リストを作る。
    通常ニュース上位5件 + 各新カテゴリから補完。
    """
    by_cat = {}
    for it in items:
        cat = it.get("category", "AI")
        by_cat.setdefault(cat, []).append(it)

    selected = []
    seen_ids = set()

    def add(item):
        if item["id"] not in seen_ids:
            seen_ids.add(item["id"])
            selected.append(item)

    # 通常ニュース上位（スコア降順）
    normal_cats = {"AI", "Research", "Industry", "Tech", "Safety", "Policy"}
    normal_items = sorted(
        [x for x in items if x.get("category") in normal_cats],
        key=lambda x: x.get("score", 5), reverse=True
    )
    for it in normal_items[:TOP_ARTICLES]:
        add(it)

    # Wow
    wow_items = sorted(by_cat.get("Wow", []), key=lambda x: x.get("score", 5), reverse=True)
    for it in wow_items[:TOP_WOW]:
        add(it)

    # Prompts
    prompt_items = sorted(by_cat.get("Prompts", []), key=lambda x: x.get("score", 5), reverse=True)
    for it in prompt_items[:TOP_PROMPTS]:
        add(it)

    # ImageVideo
    iv_items = sorted(by_cat.get("ImageVideo", []), key=lambda x: x.get("score", 5), reverse=True)
    for it in iv_items[:TOP_IMAGEVIDEO]:
        add(it)

    # Events（開催日順）
    event_items = sorted(by_cat.get("Events", []), key=lambda x: x.get("event_date") or x["date"])
    for it in event_items[:TOP_EVENTS]:
        add(it)

    return selected


def call_openrouter(items: list) -> dict | None:
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        print("  ⚠ OPENROUTER_API_KEY が未設定")
        return None

    news_list = "\n".join([
        f"[{i+1}] カテゴリ: {it.get('category','AI')} | タイトル: {it['title']}\n"
        f"    URL: {it['url']}\n"
        f"    要約: {(it.get('summary_ja') or it.get('summary',''))[:100]}\n"
        f"    ソース: {it['source']}"
        + (f"\n    イベント日程: {it.get('event_date','')} / 会場: {it.get('event_place','')}"
           if it.get("category") == "Events" else "")
        for i, it in enumerate(items)
    ])

    payload = {
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT_TEMPLATE.format(
                count=len(items),
                news_list=news_list,
            )},
        ],
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://github.com/tsukiproduct/signal-news",
        "X-Title": "SIGNAL AI News",
    }

    req = urllib.request.Request(
        OPENROUTER_API_URL,
        data=json.dumps(payload).encode(),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())

        raw_text = data["choices"][0]["message"]["content"].strip()

        if "```" in raw_text:
            parts = raw_text.split("```")
            for part in parts:
                part = part.strip()
                if part.startswith("json"):
                    part = part[4:].strip()
                if part.startswith("{"):
                    raw_text = part
                    break

        return json.loads(raw_text.strip())

    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"  ✗ OpenRouter API HTTP {e.code}: {body[:300]}")
        return None
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        print(f"  ✗ Parse error: {e}")
        return None


def build_article(article_data: dict, source_items: list, date_str: str, file_key: str = "") -> dict:
    aff_key   = article_data.get("affiliate_context", DEFAULT_AFFILIATE)
    affiliate = AFFILIATE_MAP.get(aff_key, AFFILIATE_MAP[DEFAULT_AFFILIATE])

    sources = [
        {"title": it["title"], "url": it["url"], "source": it["source"],
         "category": it.get("category", "AI")}
        for it in source_items
    ]

    return {
        "id":           f"{file_key}-{article_data.get('slug','digest')}",
        "file_key":     file_key,
        "date":         date_str,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "title":        article_data.get("title", "今日のAIダイジェスト"),
        "slug":         article_data.get("slug", "digest"),
        "summary":      article_data.get("summary", ""),
        "tags":         article_data.get("tags", []),
        "sections":     article_data.get("sections", []),
        "sources":      sources,
        "affiliate": {
            "label":      affiliate["label"],
            "url":        affiliate["url"],
            "cta":        affiliate["cta"],
            "disclosure": "※本リンクはアフィリエイトリンクです（PR）",
        },
        "legal": {
            "ai_disclosure":  "この記事はAI（OpenRouter / Llama 3.1）が生成したコンテンツを含みます。",
            "editorial_note": "事実関係は参照元記事をご確認ください。",
            "copyright_note": "引用部分の著作権は各原著作者に帰属します。",
        },
    }


def update_digests_index(article: dict) -> None:
    if DIGESTS_PATH.exists():
        index = json.loads(DIGESTS_PATH.read_text())
    else:
        index = {"articles": []}

    index["articles"] = [a for a in index["articles"] if a["id"] != article["id"]]
    index["articles"].insert(0, {
        "id":       article["id"],
        "date":     article["date"],
        "file_key": article.get("file_key", article["date"]),
        "title":    article["title"],
        "summary":  article["summary"],
        "tags":     article["tags"],
        "slug":     article["slug"],
    })

    index["articles"] = index["articles"][:MAX_DIGESTS]
    index["updated_at"] = datetime.now(timezone.utc).isoformat()
    DIGESTS_PATH.write_text(json.dumps(index, ensure_ascii=False, indent=2))


def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Phase 2.5: Generating digest via OpenRouter...")

    if not NEWS_PATH.exists():
        print(f"✗ {NEWS_PATH} が見つかりません")
        sys.exit(1)

    news  = json.loads(NEWS_PATH.read_text())
    items = news.get("items", [])

    if len(items) < 3:
        print("  ⚠ ニュースが3件未満のためスキップ")
        sys.exit(0)

    top_items = pick_top_items(items)
    print(f"  → 選択: {len(top_items)}件")
    for it in top_items:
        print(f"     [{it.get('category','?')}] {it['title'][:50]}")

    article_data = call_openrouter(top_items)

    if not article_data:
        print("  ✗ 記事生成失敗")
        sys.exit(1)

    jst     = timezone(timedelta(hours=9))
    now_jst = datetime.now(jst)
    date_str = now_jst.strftime("%Y-%m-%d")
    slot    = "morning" if now_jst.hour < 10 else "afternoon" if now_jst.hour < 16 else "evening"
    file_key = f"{date_str}_{slot}"

    article = build_article(article_data, top_items, date_str, file_key)

    ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
    article_path = ARTICLES_DIR / f"{file_key}.json"
    article_path.write_text(json.dumps(article, ensure_ascii=False, indent=2))
    print(f"  ✓ 保存 → {article_path}")

    update_digests_index(article)
    print(f"\n✅ Phase 2.5 done — 「{article['title']}」")


if __name__ == "__main__":
    main()
