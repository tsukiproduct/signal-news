"""Reader-first homepage. No operator revenue strategy in public news."""
from html import escape as e
from datetime import datetime
from amazon_offers import kindle
from daily_brief import render as briefing

SUPPORT_URL = 'https://buymeacoffee.com/tsuki_product'

def support(lang, compact=False):
    en = lang == 'en'
    title = 'Was this useful?' if en else '今日の情報整理、役に立ちましたか？'
    copy = 'Help keep SIGNAL’s news summaries available.' if en else 'ニュースを探し、整理して届ける活動を応援できます。'
    label = 'Support SIGNAL' if en else 'コーヒー1杯で応援する'
    button = f'<a class="support-button" data-signal-event="support_click" href="{SUPPORT_URL}" target="_blank" rel="noopener noreferrer">{label} ↗</a>'
    if compact:
        return f'<div class="support-inline"><p>{title}<small>{copy}</small></p>{button}</div>'
    return f'<section class="rail-block support-box"><span class="kicker">SUPPORT SIGNAL</span><h2>{title}</h2><p>{copy}</p>{button}</section>'

def render(lang, news, frame, select, card, categories, path, t):
    items = sorted(select(news.get('items', [])), key=lambda i: i.get('date',''), reverse=True)
    buttons = ''.join(f'<button type="button" data-filter="{key}" aria-pressed="{str(key=="all").lower()}">{labels[lang=="en"]}</button>' for key,labels in categories.items() if key=='all' or any(i.get('category')==key for i in items))
    updated = news.get('updated_at','')
    cards = ''.join(card(item,lang) for item in items)
    title = t(lang,'毎日5分、AIの変化をつかむ。','Your five-minute AI briefing.')
    guides = [('video-budget', '動画生成AIの料金を比較する前に', 'Before comparing video AI plans'),('local-ai','ローカルAI用PCを買う前に','Before buying local AI hardware'),('ai-learning','AIの入門書を選ぶときに','Choosing an AI book')]
    guide_links = ''.join(f'<li><a data-signal-event="guide_open" href="{path(lang,"guides/"+slug+".html")}">{t(lang,ja,en)}</a></li>' for slug,ja,en in guides)
    body = f'''<main id="main" class="wrap"><div class="edition-bar"><span>{t(lang,'AIの新機能・使い方・動向','AI releases, workflows & developments')}</span><time datetime="{e(updated)}">{t(lang,'更新','Updated')} {e(updated[:16].replace('T',' '))} UTC</time></div>
<div class="intro"><h1>{t(lang,'毎日5分、AIの変化をつかむ。','Your five-minute AI briefing.')}</h1><p>{t(lang,'新機能・料金・利用条件。自分に関係する変化を短く把握し、気になったら出典へ。','New capabilities, costs and conditions. Understand what matters to you, then explore the source.')}</p><a href="/digest.html">{t(lang,"数本まとめて読みたい方へ → まとめ読み","Read several stories together → Digest (Japanese)")}</a></div>
<p class="stale" data-updated="{e(updated)}" hidden>{t(lang,'最終更新から24時間以上経過しています。最新の条件は出典で確認してください。','This edition is more than 24 hours old. Check sources for current conditions.')}</p>
{briefing(items,lang)}<div class="feed-heading"><h2>{t(lang,"自分に関係するニュースを探す","Find what matters to you")}</h2><p>{t(lang,"カテゴリやキーワードで絞り込み。気になる記事は、この端末の「あとで読む」に保存できます。","Filter by topic or keyword. Save stories for later on this device.")}</p><p id="return-note" class="count" hidden></p></div><div class="toolbar"><label class="search">{t(lang,'ニュースを検索','Search news')}<input id="news-search" type="search" placeholder="{t(lang,'ツール名や気になるキーワード','A tool or topic you follow')}"></label><label>{t(lang,'表示する記事','Show')}<select id="news-mode"><option value="all">{t(lang,'すべて','All stories')}</option><option value="new">{t(lang,"前回以降の新着","Since your last visit")}</option><option value="saved">{t(lang,'あとで読む','Saved')}</option><option value="unread">{t(lang,'未読','Unread')}</option></select></label><label>{t(lang,'並び順','Sort')}<select id="news-sort"><option value="latest">{t(lang,'新しい順','Newest')}</option><option value="oldest">{t(lang,'古い順','Oldest')}</option><option value="useful">{t(lang,'自動評価順','Automated score')}</option></select></label><details class="display-settings"><summary>{t(lang,'文字サイズ・画面の明るさ','Text size & appearance')}</summary><button type="button" data-display="large" aria-pressed="false">{t(lang,'文字を大きく','Larger text')}</button><button type="button" data-display="dark" aria-pressed="false">{t(lang,'暗い表示','Dark theme')}</button></details></div>
<p class="count">{t(lang,"自動評価順は収集・要約処理のスコア順です。同点は新しい記事を優先します。閲覧数・SNSの人気順ではありません。","Automated order uses collection and summary scores, newest first on ties. It does not measure views or social popularity.")}</p><div class="filters" aria-label="{t(lang,'カテゴリ','Topics')}">{buttons}</div>
<noscript><p class="noscript">{t(lang,'記事はそのまま読めます。検索・保存にはJavaScriptが必要です。','Stories are readable without JavaScript. Search and saving require JavaScript.')}</p></noscript>
<div class="layout"><section aria-label="{t(lang,'ニュース一覧','News feed')}"><p id="result-count" class="count" role="status">{len(items)} {t(lang,'件の記事','stories')}</p><p id="empty" class="empty" {'hidden' if items else ''}>{t(lang,'該当する記事がありません。条件を変えてお試しください。','No matching stories. Try changing the filters.')}</p><div id="news-list">{cards}</div><nav class="pagination" id="news-pagination" aria-label="{t(lang,'記事のページ','News pages')}" hidden><button type="button" id="news-prev">{t(lang,'前へ','Previous')}</button><span id="news-page" role="status"></span><button type="button" id="news-next">{t(lang,'次へ','Next')}</button></nav>{support(lang,True)}</section>
<aside class="rail"><section class="rail-block"><span class="kicker">{t(lang,'読む、その先へ','READ FURTHER')}</span><h2>{t(lang,'AI活用ガイド','AI practical guides')}</h2><p>{t(lang,"動画制作費の計算、PC環境の確認、学習方法の整理に使えます。","Estimate video costs, check your PC setup and plan your learning.")}</p><ul class="rail-list">{guide_links}</ul></section>{kindle(lang)}{support(lang)}
<section class="rail-block ad-box"><span class="ad-label">{t(lang,'広告・協賛について','Advertising & sponsorship')}</span><p>{t(lang,'AIを使う人に、サービスや製品を届けたい方へ。','For services and products relevant to people using AI.')}</p><a href="/advertise.html">{t(lang,'掲載について','Contact about advertising')} ↗</a></section>
<section class="rail-block"><h2>{t(lang,'出典を大切に。','Keep the source in view.')}</h2><p>{t(lang,'要約にはAIを使用しています。料金や利用条件など、重要な情報は出典でも確認できます。','Summaries use AI. Follow sources to verify pricing, usage terms and other important details.')}</p><a href="{path(lang,'sources.html')}">{t(lang,'情報源・編集方針','Sources & standards')}</a></section></aside></div></main>'''
    return frame(lang,'',title,t(lang,'AIのニュースを日本語・英語で短く整理。新機能、活用方法、利用条件を出典付きで確認できます。','Concise AI news in Japanese and English. Explore new capabilities, workflows and conditions with source links.'),body)

def retired(lang, frame, path, t):
    title = t(lang,'ニュースを読む','Read the news')
    body = f'<main id="main" class="wrap article"><h1>{title}</h1><p>{t(lang,"このページの公開は終了しました。最新のAIニュースはこちらからご覧ください。","This page has been retired. Continue to the latest AI news.")}</p><a href="{path(lang)}">{t(lang,"AIニュースへ","Go to AI news")}</a></main>'
    return frame(lang,'playbook.html',title,title,body).replace('</head>','<meta name="robots" content="noindex,follow"></head>')
