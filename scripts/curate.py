#!/usr/bin/env python3
"""
AI News Curator — Phase 2 (Claude API 判断層)
役割: raw.json を読み、Claude に有用度スコア付けと要約生成を依頼する。
実行: python3 curate.py
入力: ../docs/data/raw.json
出力: ../docs/data/news.json   （フロントエンドが読む最終データ）

環境変数:
  ANTHROPIC_API_KEY  — GitHub Actions の Secrets に設定する

カテゴリ: AI / Research / Industry / Tech / Safety / Policy
          Wow / Events / Prompts / ImageVideo  ← NEW
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

RAW_PATH    = Path(__file__).parent.parent / "docs" / "data" / "raw.json"
OUTPUT_PATH = Path(__file__).parent.parent / "docs" / "data" / "news.json"

API_URL     = "https://api.anthropic.com/v1/messages"
MODEL       = "claude-haiku-4-5-20251001"
MAX_TOKENS  = 4096
BATCH_SIZE  = 20
TOP_N       = 80    # 新カテゴリ追加分を考慮して60→80に拡張
SCORE_THRESHOLD = 5

# Eventsは日付フィルタしないため除外
NON_SCORED_CATEGORIES = {"Events"}

# ════════════════════════════════════════════════
# Image/Video 自動分類キーワード
# 既存ソース（TechCrunch / Verge / HuggingFace等）の記事から
# 画像・動画生成関連のものをImageVideoカテゴリに自動昇格させる
# ════════════════════════════════════════════════
IMAGEVIDEO_KEYWORDS = [
    # 画像生成モデル
    "midjourney", "dall-e", "dalle", "stable diffusion", "stable-diffusion",
    "flux", "imagen", "ideogram", "firefly", "nano banana",
    # 動画生成モデル
    "sora", "runway", "pika labs", "kling", "veo", "lumiere",
    "luma dream", "pixverse", "minimax", "hailuo",
    # 一般用語
    "text-to-image", "text to image", "text-to-video", "text to video",
    "image generation", "video generation", "generative video",
    "diffusion model", "diffusion models",
    # 日本語
    "画像生成", "動画生成", "画像生成ai", "動画生成ai",
    "テキストから画像", "テキストから動画",
]

def reclassify_to_imagevideo(item: dict) -> bool:
    """記事のタイトル/要約をキーワードでチェックしてImageVideo該当か判定"""
    text = (item.get("title","") + " " + item.get("summary","")).lower()
    return any(kw in text for kw in IMAGEVIDEO_KEYWORDS)

SYSTEM_PROMPT = """あなたはAIニュースの専門キュレーターです。
渡された記事リストを精査し、AIに真剣に関心を持つ読者にとって有用な記事を厳選・スコアリングしてください。

【評価基準】
- 10点: 業界を揺るがす重大発表（新モデルリリース、大型資金調達、規制決定、画期的研究）
- 7〜9点: 実務・研究に直接役立つ情報（技術解説、ツール紹介、事例研究）
- 5〜6点: 一般的に興味深いAI関連ニュース
- 3〜4点: 周辺情報、PR色が強い記事
- 1〜2点: AIとほぼ無関係、広告、重複

【カテゴリ別評価の補足】
- Prompts: 実際に使えるプロンプト例・解説があるものを高評価
- ImageVideo: 画像・動画生成AIの新手法・ツール・作例を高評価
- Wow: バイラル性・驚き・HNポイント数を重視
- Events: スコアリング対象外（日程情報として全件保持）

【除外基準】
- 明らかにAIと無関係な記事
- 根拠のない誇大広告
- 重複・焼き直し記事（類似タイトルが複数あれば最も良質な1本だけ残す）

【出力形式】
必ずJSONのみを返してください。前置き・コメント・マークダウン記号は一切不要です。
{
  "results": [
    {
      "id": "記事のid（元データのまま）",
      "score": 8,
      "reason": "スコア理由（20字以内）",
      "summary_ja": "日本語で読める要約（60字以内、英語記事も日本語で）"
    }
  ]
}"""


def call_claude(items: list) -> list:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("  ⚠ ANTHROPIC_API_KEY が未設定。スコアリングをスキップします。")
        return []

    article_list = "\n".join([
        f'[{i+1}] id={it["id"]} | cat={it["category"]} | source={it["source"]} | '
        f'title={it["title"][:100]} | summary={it["summary"][:120]}'
        for i, it in enumerate(items)
    ])

    payload = {
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "system": SYSTEM_PROMPT,
        "messages": [{
            "role": "user",
            "content": f"以下の{len(items)}件の記事をスコアリングしてください:\n\n{article_list}"
        }]
    }

    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }

    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode(),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
        raw_text = data["content"][0]["text"].strip()

        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
        raw_text = raw_text.strip()

        result = json.loads(raw_text)
        return result.get("results", [])

    except (urllib.error.URLError, json.JSONDecodeError, KeyError, IndexError) as e:
        print(f"  ✗ Claude API error: {e}")
        return []


def merge_scores(raw_items: list, scored: list) -> list:
    score_map = {r["id"]: r for r in scored}
    enriched = []
    for item in raw_items:
        # Eventsはスコアリング対象外 → デフォルト値をセットしてそのまま保持
        if item.get("category") in NON_SCORED_CATEGORIES:
            item.setdefault("score", 5)
            item.setdefault("reason", "イベント情報")
            item.setdefault("summary_ja", item["summary"])
            enriched.append(item)
            continue

        s = score_map.get(item["id"])
        if s:
            item["score"]      = s.get("score", 5)
            item["reason"]     = s.get("reason", "")
            item["summary_ja"] = s.get("summary_ja", item["summary"])
        else:
            item["score"]      = 5
            item["reason"]     = "未評価"
            item["summary_ja"] = item["summary"]
        enriched.append(item)
    return enriched


def main():
    if not RAW_PATH.exists():
        print(f"✗ {RAW_PATH} が見つかりません。先に fetch_news.py を実行してください。")
        sys.exit(1)

    raw = json.loads(RAW_PATH.read_text())
    raw_items = raw.get("items", [])
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Phase 2: Curating {len(raw_items)} items via Claude API...")

    # ── 画像/動画キーワードを含む記事をImageVideoカテゴリに自動昇格 ──
    # 既存ソース（TechCrunch等）から画像生成・動画生成関連の記事を拾う
    # 元のカテゴリがWow/Events/Promptsなど特殊カテゴリの場合は触らない
    UNTOUCHED = {"Wow", "Events", "Prompts", "ImageVideo"}
    promoted_count = 0
    for item in raw_items:
        if item.get("category") in UNTOUCHED:
            continue
        if reclassify_to_imagevideo(item):
            item["category"] = "ImageVideo"
            promoted_count += 1
    if promoted_count:
        print(f"  → ImageVideo自動昇格: {promoted_count}件")

    # Events はスコアリングAPIに送らない（コスト節約・不要なため）
    score_targets = [x for x in raw_items if x.get("category") not in NON_SCORED_CATEGORIES]
    events_items  = [x for x in raw_items if x.get("category") in NON_SCORED_CATEGORIES]
    print(f"  → スコアリング対象: {len(score_targets)}件 / イベント（対象外）: {len(events_items)}件")

    # ── バッチ処理 ─────────────────────────────────────────────────────────
    all_scored = []
    for i in range(0, len(score_targets), BATCH_SIZE):
        batch = score_targets[i:i+BATCH_SIZE]
        print(f"  → Batch {i//BATCH_SIZE + 1}: {len(batch)} items")
        results = call_claude(batch)
        all_scored.extend(results)
        if i + BATCH_SIZE < len(score_targets):
            time.sleep(1.5)

    # ── マージ & フィルタリング ────────────────────────────────────────────
    enriched = merge_scores(raw_items, all_scored)

    if not all_scored:
        print("  ℹ Claude未使用 — priority + date でソートします")
        enriched.sort(key=lambda x: x["date"], reverse=True)
    else:
        # スコア閾値フィルタ（Eventsは除外しない）
        before = len(enriched)
        enriched = [
            x for x in enriched
            if x.get("category") in NON_SCORED_CATEGORIES
            or x.get("score", 5) >= SCORE_THRESHOLD
        ]
        print(f"  → Score filter: {before} → {len(enriched)} items (threshold={SCORE_THRESHOLD})")

        # カテゴリ別に並び替え
        events   = [x for x in enriched if x.get("category") == "Events"]
        others   = [x for x in enriched if x.get("category") != "Events"]

        # Events: 開催日の近い順
        events.sort(key=lambda x: x.get("event_date") or x["date"])
        # Others: スコア降順 → 同スコア内は日付降順
        others.sort(key=lambda x: (x.get("score", 5), x["date"]), reverse=True)

        enriched = others[:TOP_N] + events

    # ── 出力 ──────────────────────────────────────────────────────────────
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps({
        "updated_at":  datetime.now(timezone.utc).isoformat(),
        "fetched_at":  raw.get("fetched_at", ""),
        "total":       len(enriched),
        "curated":     bool(all_scored),
        "items":       enriched,
    }, ensure_ascii=False, indent=2))

    print(f"\n✅ Phase 2 done — {len(enriched)} curated items → {OUTPUT_PATH}")

    if all_scored:
        from collections import Counter
        dist = Counter(x.get("score", 0) for x in enriched if x.get("category") not in NON_SCORED_CATEGORIES)
        print("  Score distribution:", dict(sorted(dist.items(), reverse=True)))
        cat_dist = Counter(x.get("category") for x in enriched)
        print("  Category breakdown:", dict(sorted(cat_dist.items())))


if __name__ == "__main__":
    main()
