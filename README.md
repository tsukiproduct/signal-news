# SIGNAL — AI Intelligence Daily

AIニュース集約サイト。英語・日本語のRSSを1日3回自動取得し、GitHub Pages で静的配信。

## アーキテクチャ（3フェーズ構造）

```
Phase 1: Python（固定ロジック）
  scripts/fetch_news.py
  → 14ソースのRSSをフェッチ → docs/data/news.json に保存

Phase 2: GitHub Actions（スケジューラー）
  .github/workflows/fetch-news.yml
  → JST 07:00 / 13:00 / 20:00 に自動実行 → commit & push

Phase 3: GitHub Pages（静的配信）
  docs/ フォルダをそのまま公開
  → ブラウザが news.json を fetch して描画
```

## セットアップ手順

### 1. リポジトリ作成

```bash
# このフォルダをリポジトリのルートに配置
git init
git remote add origin https://github.com/YOUR_USERNAME/ai-news-signal.git
git add .
git commit -m "init: SIGNAL AI News Site"
git push -u origin main
```

### 2. GitHub Pages を有効化

- Settings → Pages → Source: `Deploy from a branch`
- Branch: `main` / Folder: `/docs`
- Save → 数分後に `https://YOUR_USERNAME.github.io/ai-news-signal/` で公開

### 3. Actions の確認

- Actions タブで `Fetch AI News (3x Daily)` が表示されることを確認
- `Run workflow` で手動実行してテスト

### 4. アフィリエイトリンクを設定

`docs/index.html` 内の以下を自分のIDに書き換える:

```
tag=YOUR_ASSOCIATE_ID  →  tag=あなたのAmazonアソシエイトID
```

## ローカル開発

```bash
# Python スクリプトのテスト
cd scripts
python3 fetch_news.py

# ローカルサーバーで確認
cd docs
python3 -m http.server 8080
# → http://localhost:8080
```

## RSS ソース一覧

|ソース            |言語|カテゴリ    |
|---------------|--|--------|
|OpenAI Blog    |EN|AI      |
|Google DeepMind|EN|Research|
|VentureBeat AI |EN|AI      |
|MIT Tech Review|EN|Research|
|TechCrunch AI  |EN|Industry|
|Ars Technica   |EN|Tech    |
|The Verge      |EN|Tech    |
|O’Reilly Radar |EN|Tech    |
|Ledge.ai       |JA|AI      |
|AINOW          |JA|AI      |
|ITmedia AI+    |JA|Tech    |
|Gigazine       |JA|Tech    |
|ASCII.jp       |JA|Tech    |
|マイナビニュース       |JA|Tech    |

## ファイル構成

```
.
├── .github/
│   └── workflows/
│       └── fetch-news.yml    # 1日3回スケジューラー
├── scripts/
│   └── fetch_news.py         # Phase 1: RSSフェッチ
└── docs/                     # GitHub Pages 公開フォルダ
    ├── index.html            # サイト本体
    └── data/
        └── news.json         # 自動生成データ（gitignore 不要）
```
