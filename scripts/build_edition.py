#!/usr/bin/env python3
"""Build a readable, bilingual static edition without runtime AI calls.

Source of truth: news.json, this editorial copy, and CSS/JS assets. Re-run after
each collection. Untranslated records are explicitly labelled, never disguised.
"""
import json
from html import escape
from pathlib import Path
from datetime import datetime, timezone
from editorial import select, canonical_source
from fetch_news import FEEDS

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
<link rel="stylesheet" href="/assets/edition.css"><script defer src="/assets/edition.js"></script><script defer src="/assets/revenue.js"></script><script type="application/ld+json">{structured}</script></head><body>
<a class="skip" href="#main">{t(lang,'本文へ移動','Skip to content')}</a>
<header><div class="wrap masthead"><a class="brand" href="{path(lang)}" aria-label="SIGNAL">SIGNAL<i> /</i></a><nav aria-label="{t(lang,'メイン','Main')}"><a href="{path(lang)}">{t(lang,'ニュース','News')}</a><a href="{path(lang,'playbook.html')}">{t(lang,'小さく稼ぐ実験室','Opportunity lab')}</a><a href="{path(lang,'sources.html')}">{t(lang,'情報源・編集方針','Sources & standards')}</a><a href="/digest.html">Digest · 日本語</a></nav><div class="languages" aria-label="Language">{languages}</div></div></header>
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
    items = select(news.get('items', []))
    cards = ''.join(card(it,lang) for it in items)
    buttons = ''.join(f'<button type="button" data-filter="{key}" aria-pressed="{str(key=="all").lower()}">{labels[lang=="en"]}</button>' for key,labels in CATEGORIES.items() if key=='all' or any(i.get('category')==key for i in items))
    updated = news.get('updated_at','')
    return frame(lang, '', t(lang,'使えるAIを、見極める。','Find the AI worth using.'), t(lang,'AIの新機能・使い方・制約を日英で読む。独立クリエイターと小さなチームのための実用ニュース。','Practical AI releases, workflows and limitations for independent creators and small teams. Japanese and English editions.'),f'''
<main id="main" class="wrap"><div class="edition-bar"><span>THE PRACTICAL AI EDITION</span><span>{t(lang,'データ更新','Data updated')}: <time datetime="{e(updated)}">{e(updated[:16].replace('T',' '))} UTC</time></span></div>
<div class="intro"><div><h1>{t(lang,'使えるAIを、見極める。','Find the AI worth using.')}</h1><p>{t(lang,'新機能、その使い道、見落としたくない制約。ニュースを次の一手へ。','New capabilities, practical uses, and limitations that matter. Turn news into a next step.')}</p></div></div>
<p class="stale" data-updated="{e(updated)}" hidden>{t(lang,'最終更新から24時間以上経過しています。最新の条件は出典で確認してください。','This edition is more than 24 hours old. Check the source for current conditions.')}</p>
<div class="toolbar"><label class="search">{t(lang,'記事を探す','Find a story')}<input id="news-search" type="search" placeholder="{t(lang,'モデル名・ツール名・使い道','Model, tool or use case')}"></label><label>{t(lang,'表示','Show')}<select id="news-mode"><option value="all">{t(lang,'すべて','All')}</option><option value="saved">{t(lang,'保存した記事','Saved')}</option><option value="unread">{t(lang,'未読','Unread')}</option></select></label><label>{t(lang,'並び順','Sort')}<select id="news-sort"><option value="useful">{t(lang,'選定順','Editorial order')}</option><option value="latest">{t(lang,'新しい順','Newest')}</option></select></label><button type="button" data-display="large" aria-pressed="false">{t(lang,'文字を大きく','Larger text')}</button><button type="button" data-display="light" aria-pressed="false">{t(lang,'明るい表示','Light theme')}</button></div>
<div class="filters" aria-label="{t(lang,'カテゴリ','Topics')}">{buttons}</div>
<noscript><p class="noscript">{t(lang,'記事はそのまま読めます。検索・保存にはJavaScriptが必要です。','Stories are readable without JavaScript. Search and saving require JavaScript.')}</p></noscript>
<div class="layout"><section aria-label="{t(lang,'ニュース一覧','News feed')}"><p id="result-count" class="count" role="status">{len(items)} {t(lang,'件の記事','stories')}</p><p id="empty" class="empty" {'hidden' if items else ''}>{t(lang,'該当する記事がありません。検索条件を変えるか、次回更新をお待ちください。','No matching stories. Change the filters or check back after the next update.')}</p><div id="news-list">{cards}</div></section>
<aside class="rail"><section class="rail-block feature"><span class="kicker">OPPORTUNITY LAB / 01</span><h2>{t(lang,'AIで量産する前に、誰の手間を減らす？','Before scaling AI, whose work can you simplify?')}</h2><p>{t(lang,'業界を一つに絞り、成果物を一つ作る。小さな需要を確かめる3つの実験。','One niche. One useful deliverable. Three small experiments to test demand.')}</p><a data-signal-event="guide_open" href="{path(lang,'playbook.html')}">{t(lang,'実験の手順を読む','Read the playbook')} →</a></section>
<section class="rail-block"><span class="kicker">BEFORE YOU SUBSCRIBE</span><h2>{t(lang,'月額より、完成品のコスト。','Price the finished work.')}</h2><p>{t(lang,'生成回数だけでなく、選別・修正の時間まで含めて考えます。','Count review and revision time, not just generation credits.')}</p><a href="{path(lang,'playbook.html')}#calculator">{t(lang,'時間単価を計算する','Calculate your hourly margin')} →</a><p><a href="/guides/video-budget.html">{t(lang,'動画生成の制作費計算機','Video cost calculator · 日本語')}</a></p></section>
<section class="rail-block"><span class="kicker">READ WITH CONTEXT</span><h2>{t(lang,'出典と、分からないこと。','Sources. And what we don’t know.')}</h2><p>{t(lang,'速報の要約はRSSベース。料金や利用条件は、原典の確認が必要です。','News summaries use RSS excerpts. Pricing and usage terms need verification at the source.')}</p><a href="{path(lang,'sources.html')}">{t(lang,'選定基準を見る','How we select stories')}</a></section></aside></div></main>''')

PLAYBOOK = {
 'ja': {
  'title':'AIで稼ぐ前に、小さな需要を見つける',
  'answer':'AIが作れるものからではなく、相手が毎週困っている作業から始める。業界を一つ、成果物を一つに絞り、無料の見本で需要を確認してから自動化を考える。これは未検証の事業仮説であり、収益の保証ではありません。',
  'intro':'「大量の記事」や「大量の画像」ではなく、確認・整理・手直しまで含めた小さな仕事を提案します。以下はSIGNALの編集案です。受注実績や市場調査で需要を証明したものではありません。',
  'sections':[
   ('01 / 一業種だけの更新差分レター','対象を「動画制作を請け負う個人」などに絞り、使っているツールの変更を、料金・商用条件・新機能・既存作業への影響に分けて整理する。単なるニュース翻訳ではなく「いつもの作業のどこを確認すべきか」を届ける。','候補読者に普段使うツールを3つ聞き、公式変更履歴から見本を1通作る。本人の同意を得て見てもらい、どの変更で判断が変わったかを聞く。価値がなければ業種か成果物を変える。','公式文書へのリンクと確認日を残す。規約・ライセンスを独断で断定しない。全文転載や無断の大量メール配信をしない。'),
   ('02 / 一種類の書類を、使える一覧へ','許可を得た商品資料や業務メモを、担当者が更新できる表・FAQに整理する。価値は文章生成の速さではなく、表記揺れの整理、出典の対応づけ、抜け漏れの確認に置く。','自作の架空データ10件で見本を作る。入力と出力の対応、修正が必要だった箇所、作業時間を記録する。実データの前に取扱条件と完成基準を合意する。','個人情報・社外秘を許可なく外部AIに送らない。AIの出力を原資料と照合する。専門的な判断を自動回答させない。'),
   ('03 / 動画素材の納品前チェック','一種類の納品物に絞り、字幕・固有名詞・縦横比・音量・書き出し設定のチェック表と修正メモを作る。生成する人が増えても、納品前の確認という仕事が残るかを試す。','自作の30秒動画でチェック前後の見本を作り、修正にかかった時間を計る。制作者に最も面倒なチェック項目を聞き、1項目だけを改善してみる。','実際に確認していない項目に合格を付けない。素材の権利と守秘義務を確認する。品質保証の範囲を先に決める。'),
  ],
  'test':'1週間の検証：相手の困りごとを聞く → 見本を1つ作る → 実際に使ってもらう → 修正時間まで計る → 継続して必要かを聞く。反応が薄ければ量産せず、仮説を見直します。',
  'questions':[('元手0円で始められる？','手元の機材と利用可能な無料枠で見本を作ることは考えられます。ただし時間・通信費・商用条件・上限は別です。契約前に必要な費用を確認してください。'),('不労所得になる？','最初は需要確認と品質管理が必要です。繰り返し依頼される部分が分かってから、テンプレートや更新サービスにできるか検討します。最初から放置で稼げるとは考えません。'),('アフィリエイトはどこに置く？','その作業に必要な比較記事や道具の確認箇所に、広告と明示して置きます。購入不要の方法も示し、報酬だけを理由に推薦しません。')]
 },
 'en': {
  'title':'Find a small need before selling AI output',
  'answer':'Start with a task someone struggles with every week, not with whatever AI can generate. Choose one niche and one deliverable. Test demand with a sample before automating. These are untested business hypotheses, not promises of income.',
  'intro':'Instead of mass-producing articles or images, propose a small job that includes checking, organizing and revision. The following ideas are SIGNAL editorial proposals, not validated demand or reported client results.',
  'sections':[
   ('01 / A change bulletin for one profession','Choose a narrow audience, such as independent video producers. Organize changes to their tools by pricing, commercial terms, capabilities and workflow impact. Explain what they should check in their existing process, rather than translating every announcement.','Ask a prospective reader which three tools they use. Build one sample from official changelogs, share it with permission and ask which change would affect a decision. If it has little value, change the audience or deliverable.','Keep source links and check dates. Do not make unsupported interpretations of licenses or terms. Do not republish full articles or send unsolicited bulk email.'),
   ('02 / Turn one document type into a usable reference','Organize authorized product materials or operating notes into a maintainable table or FAQ. The value is resolving inconsistent names, mapping outputs to sources and checking omissions—not simply generating prose quickly.','Build a sample with ten fictional records. Track input-to-output links, corrections and time spent. Agree on data handling and acceptance criteria before using real documents.','Never send confidential or personal data to external AI without permission. Check outputs against original records. Do not automate specialist judgments.'),
   ('03 / A pre-delivery check for video assets','Focus on one deliverable: subtitles, names, aspect ratios, audio levels or export settings. Offer a checklist and correction notes. Test whether pre-delivery review remains a useful service for creators using generation tools.','Use a 30-second video you made yourself. Create a before-and-after sample and measure correction time. Ask a creator which check is most tedious and improve that one step.','Never mark an unchecked item as passed. Confirm asset rights and confidentiality. Agree on the scope of quality assurance beforehand.'),
  ],
  'test':'A one-week experiment: ask about a problem → make one sample → let someone use it → measure review and revision time → ask whether they need it again. If the response is weak, revisit the hypothesis rather than scaling output.',
  'questions':[('Can I start with no cash?','You may be able to create a sample using existing equipment and available free tiers. Time, connectivity, commercial-use conditions and usage limits still matter. Check actual costs before accepting work.'),('Is this passive income?','Demand testing and quality control come first. Once a repeat need emerges, consider templates or an update service. Do not assume an unattended system will earn money.'),('Where should affiliate links go?','Place clearly disclosed links where readers compare tools needed for the task. Explain no-purchase alternatives. Do not recommend a tool merely because it pays a commission.')]
 }
}

def playbook(lang):
    copy = PLAYBOOK[lang]
    sections = ''.join(f'<section><h2>{e(heading)}</h2><p>{e(idea)}</p><h3>{t(lang,"最小の実験","Smallest test")}</h3><p>{e(test)}</p><h3>{t(lang,"落とし穴","Limitations")}</h3><p>{e(caution)}</p></section>' for heading,idea,test,caution in copy['sections'])
    faq = ''.join(f'<h3>{e(q)}</h3><p>{e(a)}</p>' for q,a in copy['questions'])
    labels = [('price','見積金額（円）','Proposed price (JPY)','0','100000000','1','5000'),('cost','外部費用（円）','External costs (JPY)','0','100000000','1','500'),('hours','確認・修正を含む総作業時間','Total hours, including review','0.1','100000','0.1','3')]
    inputs = ''.join(f'<label>{t(lang,ja,en)}<input name="{name}" type="number" min="{mn}" max="{mx}" step="{step}" value="{value}" required></label>' for name,ja,en,mn,mx,step,value in labels)
    body = f'''<main id="main" class="wrap article"><p class="kicker">SIGNAL / OPPORTUNITY LAB</p><h1>{e(copy['title'])}</h1><p class="meta">TSUKI PRODUCT · {t(lang,'編集案・未検証の仮説','Editorial proposals · untested hypotheses')}</p><p class="answer">{e(copy['answer'])}</p><p>{e(copy['intro'])}</p>{sections}<h2>{t(lang,'量産する前の判断','Before you scale')}</h2><p>{e(copy['test'])}</p><section id="calculator"><h2>{t(lang,'修正時間も入れると、いくら残る？','What remains after revision time?')}</h2><p>{t(lang,'初期値は説明用です。市場相場・予測収益ではありません。金額から外部費用を引き、作業時間で割ります。','Defaults are illustrative, not market rates or income forecasts. Subtract external costs from the proposed price, then divide by hours worked.')}</p><form id="margin-calculator">{inputs}<output id="margin-result" aria-live="polite">{t(lang,'計算にはJavaScriptを有効にしてください。','Enable JavaScript to calculate.')}</output></form><p>{t(lang,'営業・学習時間、税金、機材費など未入力の費用は含まれません。入力は外部送信しません。','Unentered sales time, learning time, taxes and equipment costs are excluded. Inputs are not sent anywhere.')}</p></section><h2>{t(lang,'よくある疑問','Common questions')}</h2>{faq}<h2>{t(lang,'次に読む','Read next')}</h2><p><a href="/guides/video-budget.html">{t(lang,'動画生成の費用を計算する','Video generation cost guide · 日本語')}</a> · <a href="/guides/local-ai.html">{t(lang,'ローカルAI用PCを買う前に','Local AI hardware checklist · 日本語')}</a></p></main>'''
    schema = {'@context':'https://schema.org','@type':'Article','headline':copy['title'],'description':copy['answer'],'inLanguage':lang,'author':{'@type':'Organization','name':'TSUKI PRODUCT'},'publisher':{'@type':'Organization','name':'SIGNAL'},'mainEntityOfPage':ORIGIN+path(lang,'playbook.html')}
    return frame(lang,'playbook.html',copy['title'],copy['answer'],body,schema)

def sources(lang):
    feeds = ''.join(f'<li><a href="{e(f["url"])}" rel="noopener">{e(f["source"])}</a> · {e(f["lang"].upper())}</li>' for f in FEEDS)
    title = t(lang,'情報源と編集方針','Sources and editorial standards')
    text = t(lang,
      '収集対象は以下の公開RSSです。接続成功や毎回の記事採用を保証する一覧ではありません。イベント、無関係な一般ニュース、古い記事、同一URL・同一見出しの重複を除外します。AI利用者への実用性を優先し、資金調達や話題性だけでは上位にしません。',
      'The following public RSS feeds are configured for collection; this is not a guarantee that every feed succeeds or every story is included. We exclude events, unrelated news, old items and duplicate URLs or headlines. We prioritize practical value for AI users over funding announcements or popularity alone.')
    body = f'''<main id="main" class="wrap article"><p class="kicker">SIGNAL / TRANSPARENCY</p><h1>{title}</h1><p class="answer">{text}</p><h2>{t(lang,'何を読んで、何を書いているか','What we read and what we write')}</h2><p>{t(lang,'AIに渡すのはRSSの見出しと短い抜粋です。記事全文を読んだ実機レビューではありません。AIは独自の短い要約、対象読者、試す手順の提案、確認すべき点を作成します。機械翻訳には誤りがあり得ます。訳が未作成の記事は原文と表示します。','AI receives RSS headlines and short excerpts, not full articles or hands-on test results. It produces short original summaries, suggested audiences, test ideas and caveats. Machine translation can be wrong. Missing translations are labelled as original-language content.')}</p><h2>{t(lang,'失敗したときの扱い','When collection or translation fails')}</h2><p>{t(lang,'翻訳APIの失敗時に架空の翻訳を埋めません。更新時刻を表示し、古くなった版には注意を出します。翻訳は設定済みAPIを使い、処理対象は1更新あたり最大60件。Anthropicの鍵がなければ設定済みOpenRouterの無料ルーターを使います。無料枠の利用可能性は保証されません。','We do not invent translations when an API fails. The edition shows its data timestamp and warns when stale. Translation is capped at 60 candidates per update. The configured Anthropic service is used when available, otherwise the configured OpenRouter free router. Free-tier availability is not guaranteed.')}</p><h2>{t(lang,'広告と独立性','Advertising and independence')}</h2><p>{t(lang,'広告・紹介リンクは明示します。広告主は通常の記事順位を購入できません。商品の購入を必要としない方法も示します。出典の転載条件・アクセス制限を尊重し、削除・訂正の依頼を受け付けます。','Advertising and affiliate links are disclosed. Advertisers cannot buy ordinary news ranking. We include no-purchase alternatives, respect source reuse conditions and access restrictions, and accept removal or correction requests.')}</p><h2>{t(lang,'収集対象','Configured feeds')}</h2><ul class="source-list">{feeds}</ul><h2>{t(lang,'訂正・配信停止のご連絡','Corrections and source removal')}</h2><p><a href="mailto:tsuki.product@gmail.com">tsuki.product@gmail.com</a></p><p>{t(lang,'該当URLと修正すべき箇所をお知らせください。','Please include the relevant URL and the passage that needs attention.')}</p></main>'''
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
    routes = ['', 'en/', 'playbook.html', 'en/playbook.html', 'sources.html', 'en/sources.html', 'guides.html','guides/video-budget.html','guides/local-ai.html','guides/ai-learning.html','advertise.html','policy.html', 'en/guides.html','en/guides/video-budget.html','en/guides/local-ai.html','en/guides/ai-learning.html']
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join(f'<url><loc>{ORIGIN}/{r}</loc></url>\n' for r in routes) + '</urlset>\n'
    (DOCS/'sitemap.xml').write_text(sitemap)
    (DOCS/'robots.txt').write_text(f'User-agent: *\nAllow: /\nSitemap: {ORIGIN}/sitemap.xml\n')
    print(f'Built six bilingual pages, sitemap and robots; {len(select(news.get("items",[])))} eligible stories per edition.')

if __name__ == '__main__':
    main()
