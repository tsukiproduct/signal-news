#!/usr/bin/env python3
"""
SIGNAL Digest Generator — Phase 2.5
OpenRouter API（無料モデル）使用版

無料モデル: meta-llama/llama-3.1-8b-instruct:free
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
MODEL     = "meta-llama/llama-3.1-8b-instruct:free"
MAX_TOKENS = 3000
TEMPERATURE = 0.7

TOP_ARTICLES = 5
MAX_DIGESTS  = 30

SYSTEM_PROMPT = """あなたはAI技術の専門ジャーナリストです。
提供されたAIニュースをもとに、読者に役立つオリジナル解説記事を日本語で書いてください。

ルール:
- 元記事の文章をそのまま転載しない
- タイトルとURLは出典として明示する
- 解説・考察・応用は自分の言葉で書く
- 事実と考察を明確に区別する
- 誇大な表現を避ける

出力はJSONのみ。前置き不要。"""

USER_PROMPT_TEMPLATE = """{count}本のAIニュースをもとに解説記事を生成してください。

【参照ニュース】
{news_list}

【出力JSON】
{{
  "title": "記事タイトル（40字以内）",
  "slug": "english-slug",
  "summary": "要約（80字以内）",
  "sections": [
    {{
      "type": "overview",
      "heading": "今日のAIニュース概観",
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
      "type": "practical",
      "heading": "実践：ビジネスへの応用",
      "body": "具体的な活用方法（300字程度）"
    }},
    {{
      "type": "prompt_of_day",
      "heading": "今日のプロンプト",
      "prompt_title": "プロンプトタイトル（20字以内）",
      "prompt_body": "実用的なプロンプト（150字程度）",
      "prompt_usecase": "使い方（100字程度）"
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
        "url": "https://www.amazon.co.jp/s?k=人工知能+機械学習+入門&tag=YOUR_ASSOCIATE_ID",
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
        "url": "https://www.amazon.co.jp/s?k=プロンプトエンジニアリング&tag=YOUR_ASSOCIATE_ID",
        "cta": "Amazon で探す →",
    },
}
DEFAULT_AFFILIATE = "機械学習コース"


def call_openrouter(items: list) -> dict | None:
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        print("  ⚠ OPENROUTER_API_KEY が未設定")
        return None

    news_list = "\n".join([
        f"[{i+1}] タイトル: {it['title']}\n"
        f"    URL: {it['url']}\n"
        f"    要約: {(it.get('summary_ja') or it.get('summary',''))[:100]}\n"
        f"    ソース: {it['source']}"
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

        # JSONフェンス除去
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
    aff_key = article_data.get("affiliate_context", DEFAULT_AFFILIATE)
    affiliate = AFFILIATE_MAP.get(aff_key, AFFILIATE_MAP[DEFAULT_AFFILIATE])

    sources = [
        {"title": it["title"], "url": it["url"], "source": it["source"]}
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

    news = json.loads(NEWS_PATH.read_text())
    items = news.get("items", [])

    if len(items) < 3:
        print("  ⚠ ニュースが3件未満のためスキップ")
        sys.exit(0)

    top_items = sorted(items, key=lambda x: x.get("score", 5), reverse=True)[:TOP_ARTICLES]
    print(f"  → 選択ニュース: {len(top_items)}件")

    article_data = call_openrouter(top_items)

    if not article_data:
        print("  ✗ 記事生成失敗")
        sys.exit(1)

    jst = timezone(timedelta(hours=9))
    now_jst = datetime.now(jst)
    date_str = now_jst.strftime("%Y-%m-%d")
    slot = "morning" if now_jst.hour < 10 else "afternoon" if now_jst.hour < 16 else "evening"
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
