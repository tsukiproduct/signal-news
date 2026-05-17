#!/usr/bin/env python3
"""
SIGNAL Digest Generator — Phase 2.5
役割: curate済みのnews.jsonからGroq APIを使ってオリジナル解説記事を生成する。

【リーガル設計】
- 元記事の内容は「タイトル + URL + 公開済み要約の一文」のみ引用
- 解説・応用・プロンプトはAIが独自に生成（完全オリジナル）
- 引用元URLを必ず明示（著作権法32条の引用要件を満たす）
- AI生成コンテンツ・PR表示を記事に自動付与（景表法対応）

実行: python3 generate_digest.py
入力: ../docs/data/news.json
出力: ../docs/articles/YYYY-MM-DD.json
      ../docs/data/digests.json（記事一覧インデックス）

環境変数:
  GROQ_API_KEY — GitHub Actions Secrets に設定
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ── パス設定 ──────────────────────────────────────────────────────────────
NEWS_PATH    = Path(__file__).parent.parent / "docs" / "data" / "news.json"
ARTICLES_DIR = Path(__file__).parent.parent / "docs" / "articles"
DIGESTS_PATH = Path(__file__).parent.parent / "docs" / "data" / "digests.json"

# ── Groq API 設定 ──────────────────────────────────────────────────────────
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL        = "llama-3.3-70b-versatile"   # Groq無料枠で最高品質
MAX_TOKENS   = 3000
TEMPERATURE  = 0.7

# ── 記事設定 ───────────────────────────────────────────────────────────────
TOP_ARTICLES   = 5    # 1回の生成で使うニュース件数
MAX_DIGESTS    = 30   # インデックスに保持する記事数（古いものは自動削除）

# ── システムプロンプト ─────────────────────────────────────────────────────
SYSTEM_PROMPT = """あなたはAI技術の専門ジャーナリスト兼エディターです。
提供されたAIニュースの情報（タイトル・URL・要約）をもとに、
読者に本当に役立つオリジナル解説記事を日本語で執筆してください。

【執筆ルール】
1. 元記事の文章をそのまま転載しない（著作権遵守）
2. タイトルとURLは出典として明示する（引用の適法要件）
3. 解説・考察・応用は完全に自分の言葉で書く
4. 技術的に正確かつ、初心者にもわかる平易な表現を使う
5. プロンプト例は実際に使える具体的なものにする

【必ず守ること】
- 事実と考察を明確に区別する（「〜と報告されています」「筆者の考えでは」等）
- 誇大な表現を避ける（「革命的」「完璧」等はNG）
- 不確かな情報に断定的な表現を使わない

出力はJSON形式のみ。前置き・マークダウン記号は不要。"""

USER_PROMPT_TEMPLATE = """以下の{count}本のAIニュースをもとに、今日の解説記事を生成してください。

【参照ニュース】
{news_list}

【出力JSON形式】
{{
  "title": "記事タイトル（40字以内・具体的で興味を引くもの）",
  "slug": "article-slug-in-english",
  "summary": "記事の要約（80字以内）",
  "sections": [
    {{
      "type": "overview",
      "heading": "今日のAIニュース概観",
      "body": "今日のAIシーンを俯瞰する導入文（200字程度）"
    }},
    {{
      "type": "deep_dive",
      "heading": "注目トピック詳説",
      "body": "最も重要なニュースの背景・意味・業界への影響を解説（400字程度）",
      "source_title": "参照した記事タイトル",
      "source_url": "参照した記事URL"
    }},
    {{
      "type": "practical",
      "heading": "実践：あなたのビジネスへの応用",
      "body": "今日のニュースを踏まえた具体的な活用方法・アクション提案（300字程度）"
    }},
    {{
      "type": "prompt_of_day",
      "heading": "今日のプロンプト",
      "prompt_title": "プロンプトのタイトル（20字以内）",
      "prompt_body": "今日のテーマに関連した実用的なプロンプト（150字程度・そのままChatGPT等に使える形式）",
      "prompt_usecase": "このプロンプトの使い方・期待できる出力（100字程度）"
    }},
    {{
      "type": "weekly_watch",
      "heading": "今週注目すべきこと",
      "body": "今日のニュースから見えてくるトレンド・今後の展望（200字程度）"
    }}
  ],
  "tags": ["タグ1", "タグ2", "タグ3"],
  "affiliate_context": "記事テーマに関連するアフィリエイト商品カテゴリ（例: AI入門書, 機械学習コース, クラウドGPU）"
}}"""

# ── アフィリエイトマッピング ───────────────────────────────────────────────
# 記事テーマに応じて関連アフィリエイトリンクを自動選択
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
    "LLMツール": {
        "label": "AI開発ツール・APIリソースまとめ",
        "url": "https://www.amazon.co.jp/s?k=LLM+Python+開発&tag=YOUR_ASSOCIATE_ID",
        "cta": "関連書籍を見る →",
    },
}
DEFAULT_AFFILIATE = "機械学習コース"


def call_groq(news_items: list) -> dict | None:
    """Groq APIを呼び出して記事JSONを返す"""
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        print("  ⚠ GROQ_API_KEY が未設定")
        return None

    # ニュースリストを整形（タイトル・URL・要約のみ — 著作権配慮）
    news_list = "\n".join([
        f"[{i+1}] タイトル: {it['title']}\n"
        f"    URL: {it['url']}\n"
        f"    要約（公開情報）: {(it.get('summary_ja') or it.get('summary',''))[:100]}\n"
        f"    ソース: {it['source']} | カテゴリ: {it['category']}"
        for i, it in enumerate(news_items)
    ])

    payload = {
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": USER_PROMPT_TEMPLATE.format(
                count=len(news_items),
                news_list=news_list,
            )},
        ],
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    req = urllib.request.Request(
        GROQ_API_URL,
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
        print(f"  ✗ Groq API HTTP {e.code}: {body[:200]}")
        return None
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        print(f"  ✗ Parse error: {e}")
        return None


def build_article(article_data: dict, source_items: list, date_str: str, file_key: str = "") -> dict:
    """Groqの生成データに메타情報・法的表示を付加して完成記事にする"""

    # アフィリエイト選択
    aff_key = article_data.get("affiliate_context", DEFAULT_AFFILIATE)
    affiliate = AFFILIATE_MAP.get(aff_key, AFFILIATE_MAP[DEFAULT_AFFILIATE])

    # 参照記事リスト（出典明示 — 引用の適法要件）
    sources = [
        {"title": it["title"], "url": it["url"], "source": it["source"]}
        for it in source_items
    ]

    return {
        # メタ情報
        "id":           f"{file_key}-{article_data.get('slug','digest')}",
        "file_key":     file_key,
        "date":         date_str,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "title":        article_data.get("title", "今日のAIダイジェスト"),
        "slug":         article_data.get("slug", "digest"),
        "summary":      article_data.get("summary", ""),
        "tags":         article_data.get("tags", []),

        # 本文セクション
        "sections":     article_data.get("sections", []),

        # 出典リスト（著作権法上の引用表示）
        "sources":      sources,

        # アフィリエイト（PR表示付き）
        "affiliate": {
            "label": affiliate["label"],
            "url":   affiliate["url"],
            "cta":   affiliate["cta"],
            "disclosure": "※本リンクはアフィリエイトリンクです（PR）",
        },

        # 法的表示（景表法・AI生成コンテンツ開示）
        "legal": {
            "ai_disclosure":   "この記事はAI（Groq / Llama 3.3）が生成したコンテンツを含みます。",
            "editorial_note":  "事実関係は参照元記事をご確認ください。本記事の解説・考察は編集部の見解です。",
            "copyright_note":  "引用部分の著作権は各原著作者に帰属します。",
        },
    }


def update_digests_index(article: dict) -> None:
    """digests.json のインデックスを更新する"""
    if DIGESTS_PATH.exists():
        index = json.loads(DIGESTS_PATH.read_text())
    else:
        index = {"articles": []}

    # 既存の同一IDを削除してから先頭に追加
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

    # MAX_DIGESTS件に制限
    index["articles"] = index["articles"][:MAX_DIGESTS]
    index["updated_at"] = datetime.now(timezone.utc).isoformat()

    DIGESTS_PATH.write_text(json.dumps(index, ensure_ascii=False, indent=2))


def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Phase 2.5: Generating digest article via Groq...")

    # ── news.json 読み込み ──────────────────────────────────────────────
    if not NEWS_PATH.exists():
        print(f"✗ {NEWS_PATH} が見つかりません")
        sys.exit(1)

    news = json.loads(NEWS_PATH.read_text())
    items = news.get("items", [])

    if len(items) < 3:
        print("  ⚠ ニュースが3件未満のためスキップします")
        sys.exit(0)

    # スコアが高い順にTOP_ARTICLES件を選択
    top_items = sorted(items, key=lambda x: x.get("score", 5), reverse=True)[:TOP_ARTICLES]
    print(f"  → 選択ニュース: {len(top_items)}件（スコア上位）")

    # ── Groq API 呼び出し ───────────────────────────────────────────────
    article_data = call_groq(top_items)

    if not article_data:
        print("  ✗ 記事生成に失敗しました")
        sys.exit(1)

    # ── 記事データを構築 ────────────────────────────────────────────────
    jst = timezone(timedelta(hours=9))
    now_jst = datetime.now(jst)
    date_str = now_jst.strftime("%Y-%m-%d")
    slot = "morning" if now_jst.hour < 10 else "afternoon" if now_jst.hour < 16 else "evening"
    file_key = f"{date_str}_{slot}"
    article = build_article(article_data, top_items, date_str, file_key)

    # ── 保存 ───────────────────────────────────────────────────────────
    ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
    article_path = ARTICLES_DIR / f"{file_key}.json"
    article_path.write_text(json.dumps(article, ensure_ascii=False, indent=2))
    print(f"  ✓ Article saved → {article_path}")

    update_digests_index(article)
    print(f"  ✓ Digests index updated → {DIGESTS_PATH}")

    print(f"\n✅ Phase 2.5 done — 「{article['title']}」")


if __name__ == "__main__":
    main()
