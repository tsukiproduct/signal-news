#!/usr/bin/env python3
"""Build a readable, bilingual static edition without runtime AI calls.

Source of truth: news.json, this editorial copy, and CSS/JS assets. Re-run after
each collection. Untranslated records are explicitly labelled, never disguised.
"""
import json
import re
from html import unescape
from html import escape
from pathlib import Path
from datetime import datetime, timezone
from editorial import select, canonical_source
from fetch_news import FEEDS
from reader_edition import support

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / 'docs'
ORIGIN = 'https://signal.tsukilab.jp'
CATEGORIES = {
    'all': ('すべて', 'All stories'), 'ImageVideo': ('画像・動画', 'Image & video'),
    'Prompts': ('使い方・開発', 'Workflows & code'), 'Research': ('モデル・研究', 'Models & research'),
    'Tech': ('ツール', 'Tools'), 'AI': ('AI活用', 'AI practice'),
    'Industry': ('ビジネス', 'Business'), 'Safety': ('安全性', 'Safety'),
    'Policy': ('ルール', 'Policy'), 'Wow': ('コミュニティ', 'Community'),
}

def e(value):
    return escape(str(value), quote=True)

def path(lang, page=''):
    return ('/en/' if lang == 'en' else '/') + page

def t(lang, ja, en):
    return en if lang == 'en' else ja

def frame(lang, page, title, description, body, schema=None):
    url = ORIGIN + path(lang, page)
    alternate = ''.join(f'<link rel="alternate" hreflang="{l}" href="{ORIGIN}{path(l, page)}">' for l in ('ja','en'))
    languages = ''.join(f'<a href="{path(l,page)}" lang="{l}" hreflang="{l}" '+('aria-current="page"' if l == lang else '')+f'>{label}</a>' for l,label in [('ja','日本語'),('en','English')])
    structured = json.dumps(schema or {'@context':'https://schema.org','@type':'WebPage','name':title,'url':url,'inLanguage':lang,'description':description}, ensure_ascii=False).replace('<','\\u003c')
    html = f'''<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)} | SIGNAL</title><meta name="description" content="{e(description)}"><link rel="canonical" href="{url}">{alternate}<link rel="alternate" hreflang="x-default" href="{ORIGIN}{path('ja',page)}">
<meta property="og:title" content="{e(title)} | SIGNAL"><meta property="og:description" content="{e(description)}"><meta property="og:url" content="{url}"><meta property="og:type" content="website"><meta property="og:image" content="{ORIGIN}/og-image.PNG"><meta name="twitter:card" content="summary_large_image">
<link rel="stylesheet" href="/assets/reader.css"><script defer src="/assets/edition.js"></script><script defer src="/assets/revenue.js"></script><script type="application/ld+json">{structured}</script></head><body>
<a class="skip" href="#main">{t(lang,'本文へ移動','Skip to content')}</a>
<header><div class="wrap masthead"><div><a class="brand" href="{path(lang)}" aria-label="SIGNAL">signal<i>.</i></a><p class="brand-note">{t(lang,'AIのニュースを、日々の理解に。','AI news for everyday understanding.')}</p></div><div class="languages" aria-label="Language">{languages}</div><nav aria-label="{t(lang,'メイン','Main')}"><a href="{path(lang)}">{t(lang,'ニュース','News')}</a><a href="{path(lang,'guides.html')}">{t(lang,'選び方ガイド','Buying guides')}</a><a href="/digest.html">{t(lang,'まとめ読み','Digest · 日本語')}</a><a href="{path(lang,'sources.html')}">{t(lang,'情報源・編集方針','Sources & standards')}</a><a href="https://buymeacoffee.com/tsuki_product" data-signal-event="support_click" target="_blank" rel="noopener noreferrer">{t(lang,'SIGNALを応援','Support SIGNAL')}</a></nav></div></header>
{body}
<footer><div class="wrap"><nav><a href="{path(lang,'sources.html')}">{t(lang,'情報源・編集方針','Sources & standards')}</a><a href="/guides.html">{t(lang,'用途別ガイド','Buying guides · 日本語')}</a><a href="/advertise.html">{t(lang,'広告掲載の相談','Advertising · 日本語')}</a><a href="mailto:tsuki.product@gmail.com">{t(lang,'お問い合わせ・訂正','Contact / corrections')}</a></nav><p>{t(lang,'RSSの見出し・抜粋に基づくAI要約・機械翻訳を含みます。原文の全文翻訳ではありません。提案は未検証の編集案です。重要な条件は出典で確認してください。','Includes AI summaries and machine translations based on RSS headlines and excerpts, not full-article translations. Suggested actions are untested editorial ideas. Verify important conditions with the source.')}</p><p>{t(lang,'保存した記事・既読・表示設定はこの端末内だけに保存します。アクセス解析の集計先は未導入です。','Saved stories, reading history and display preferences stay on this device. No analytics collector has been added.')} {t(lang,'Amazonのアソシエイトとして、TSUKI PRODUCTは適格販売により収入を得ています。','As an Amazon Associate, TSUKI PRODUCT earns from qualifying purchases.')}</p><p>© TSUKI PRODUCT · SIGNAL</p></div></footer></body></html>'''

    if lang == 'en':
        html = html.replace('href="/guides/', 'href="/en/guides/').replace('href="/guides.html"', 'href="/en/guides.html"')
        for label in ('Buying guides', 'Video cost calculator', 'Video generation cost guide', 'Local AI hardware checklist'):
            html = html.replace(label + ' · 日本語', label)
    return html

def localized(item, field, lang):
    translated = item.get(f'{field}_{lang}')
    # Legacy summary_ja often contains untouched English RSS. Do not treat it
    # as a translation without an accompanying translated title.
    if translated and (field != 'summary' or item.get(f'title_{lang}') or item.get('lang') == lang):
        return translated, lang
    return item.get(field, ''), item.get('lang', 'en')

def card(item, lang):
    title, title_lang = localized(item, 'title', lang)
    summary, summary_lang = localized(item, 'summary', lang)
    category = item.get('category', 'AI')
    label = CATEGORIES.get(category, (category, category))[lang == 'en']
    url = canonical_source(item.get('url',''))
    translated = title_lang == lang and summary_lang == lang
    status = t(lang,'AI要約・機械翻訳／RSSベース','AI summary / translation · RSS-based') if item.get('translation_status') == 'machine' else t(lang,'原文の見出し・RSS抜粋','Original headline / RSS excerpt')
    if not translated:
        status += t(lang,' · 日本語訳は準備中',' · English translation pending')
    bits = []
    for key, ja, en in [('useful_for','誰に役立つ？','Who is this for?'),('try_next','試すなら（提案）','Try next (suggestion)'),('caveat','確認すべき点','Check first')]:
        value = item.get(f'{key}_{lang}')
        if value:
            bits.append(f'<dt>{t(lang,ja,en)}</dt><dd>{e(value)}</dd>')
    details = f'<details><summary>{t(lang,"実務で使う前に","Before you use it")}</summary><dl>{"".join(bits)}</dl></details>' if bits else ''
    return f'''<article class="news-card" data-id="{e(item['id'])}" data-category="{e(category)}" data-date="{e(item.get('date',''))}" data-score="{e(item.get('score',5))}">
<div class="meta"><span class="topic">{e(label)}</span><span>{e(item.get('source',''))}</span><time datetime="{e(item.get('date',''))}">{e(item.get('date','')[:10])}</time></div>
<h2 lang="{e(title_lang)}"><a data-original href="{e(url)}" target="_blank" rel="noopener noreferrer">{e(title)}</a></h2>
<p class="summary" lang="{e(summary_lang)}">{e(summary)}</p><p class="translation">{status}</p>{details}
<div class="card-foot"><a class="source-link" data-original href="{e(url)}" target="_blank" rel="noopener noreferrer">{t(lang,'出典を読む','Read source')} · {e(item.get('lang','').upper())} ↗</a><button type="button" class="save" aria-pressed="false">{t(lang,'あとで読む','Save')}</button></div></article>'''

def home(lang, news):
    from reader_edition import render
    return render(lang, news, frame, select, card, CATEGORIES, path, t)

def playbook(lang):
    from reader_edition import retired
    return retired(lang, frame, path, t)

def sources(lang):
    feeds = ''.join(f'<li><a href="{e(f["url"])}" rel="noopener">{e(f["source"])}</a> · {e(f["lang"].upper())}</li>' for f in FEEDS)
    title = t(lang,'情報源と編集方針','Sources and editorial standards')
    text = t(lang,
      '収集対象は以下の公開RSSです。接続成功や毎回の記事採用を保証する一覧ではありません。イベント、無関係な一般ニュース、古い記事、同一URL・同一見出しの重複を除外します。AI利用者への実用性を優先し、資金調達や話題性だけでは上位にしません。',
      'The following public RSS feeds are configured for collection; this is not a guarantee that every feed succeeds or every story is included. We exclude events, unrelated news, old items and duplicate URLs or headlines. We prioritize practical value for AI users over funding announcements or popularity alone.')
    body = f'''<main id="main" class="wrap article"><p class="kicker">SIGNAL / TRANSPARENCY</p><h1>{title}</h1><p class="answer">{text}</p><h2>{t(lang,'何を読んで、何を書いているか','What we read and what we write')}</h2><p>{t(lang,'AIに渡すのはRSSの見出しと短い抜粋です。記事全文を読んだ実機レビューではありません。AIは独自の短い要約、対象読者、試す手順の提案、確認すべき点を作成します。機械翻訳には誤りがあり得ます。訳が未作成の記事は原文と表示します。','AI receives RSS headlines and short excerpts, not full articles or hands-on test results. It produces short original summaries, suggested audiences, test ideas and caveats. Machine translation can be wrong. Missing translations are labelled as original-language content.')}</p><h2>{t(lang,'失敗したときの扱い','When collection or translation fails')}</h2><p>{t(lang,'翻訳APIの失敗時に架空の翻訳を埋めません。更新時刻を表示し、古くなった版には注意を出します。翻訳が用意できない場合は原文と明示します。','We do not invent translations when an API fails. The edition shows its data timestamp and warns when stale. If a translation is unavailable, we label the original-language text.')}</p><h2>{t(lang,'広告と独立性','Advertising and independence')}</h2><p>{t(lang,'広告・紹介リンクは明示します。広告主は通常の記事順位を購入できません。商品の購入を必要としない方法も示します。出典の転載条件・アクセス制限を尊重し、削除・訂正の依頼を受け付けます。','Advertising and affiliate links are disclosed. Advertisers cannot buy ordinary news ranking. We include no-purchase alternatives, respect source reuse conditions and access restrictions, and accept removal or correction requests.')}</p><h2>{t(lang,'収集対象','Configured feeds')}</h2><ul class="source-list">{feeds}</ul><h2>{t(lang,'訂正・配信停止のご連絡','Corrections and source removal')}</h2><p><a href="mailto:tsuki.product@gmail.com">tsuki.product@gmail.com</a></p><p>{t(lang,'該当URLと修正すべき箇所をお知らせください。','Please include the relevant URL and the passage that needs attention.')}</p></main>'''
    return frame(lang,'sources.html',title,text,body)

def main():
    news = json.loads((DOCS/'data/news.json').read_text())
    seed_path = DOCS/'data/translation_seed.json'
    seeds = json.loads(seed_path.read_text()) if seed_path.exists() else {}
    for item in news.get('items', []):
        if item.get('translation_status') != 'machine' and item.get('id') in seeds:
            item.update(seeds[item['id']])
            if item.get('try_next_ja') and item.get('try_next_en'):
                item['score'] = max(item.get('score',5), 7)
    for lang in ('ja','en'):
        for name, html in [('index.html',home(lang,news)),('playbook.html',playbook(lang)),('sources.html',sources(lang))]:
            target = DOCS / ('en' if lang=='en' else '') / name
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_text(html,encoding='utf-8')
    from english_guides import build
    build(DOCS, frame, ORIGIN)
    # Bring original Japanese guides into the same reading layout, retaining
    # their content, calculator IDs and partner-renderer markers.
    for rel in ('guides.html','guides/video-budget.html','guides/local-ai.html','guides/ai-learning.html'):
        target = DOCS/rel
        original = target.read_text()
        main_body = re.search(r'<main\b[^>]*>(.*?)</main>', original, re.S)
        title_match = re.search(r'<title>(.*?)</title>', original, re.S)
        if not main_body or not title_match:
            raise ValueError(f'Missing guide content: {rel}')
        title = unescape(title_match[1]).split(' | SIGNAL')[0]
        target.write_text(frame('ja',rel,title,title,'<main id="main" class="wrap article">'+main_body[1]+'</main>'))
    digest_path = DOCS/'digest.html'
    digest = digest_path.read_text()
    if 'data-reader-support' not in digest:
        digest = digest.replace('<div class="footer-links">','<div class="footer-links"><a data-reader-support data-signal-event="support_click" href="https://buymeacoffee.com/tsuki_product" target="_blank" rel="noopener noreferrer">SIGNALを応援する</a>')
        digest_path.write_text(digest)
    routes = ['', 'en/', 'sources.html', 'en/sources.html', 'guides.html','guides/video-budget.html','guides/local-ai.html','guides/ai-learning.html','advertise.html','policy.html', 'en/guides.html','en/guides/video-budget.html','en/guides/local-ai.html','en/guides/ai-learning.html']
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join(f'<url><loc>{ORIGIN}/{r}</loc></url>\n' for r in routes) + '</urlset>\n'
    (DOCS/'sitemap.xml').write_text(sitemap)
    (DOCS/'robots.txt').write_text(f'User-agent: *\nAllow: /\nSitemap: {ORIGIN}/sitemap.xml\n')
    print(f'Built six bilingual pages, sitemap and robots; {len(select(news.get("items",[])))} eligible stories per edition.')

if __name__ == '__main__':
    main()
