"""A bounded, source-linked briefing from recent translated stories."""
from datetime import datetime, timezone, timedelta
from html import escape as e
from editorial import canonical_source

def picks(items, now=None):
    now = now or datetime.now(timezone.utc)
    result=[]; sources=set()
    for item in sorted(items,key=lambda i:(i.get('score',0),i.get('date','')),reverse=True):
        try: fresh = now-timedelta(hours=72)<=datetime.fromisoformat(item['date'].replace('Z','+00:00'))<=now
        except (ValueError,KeyError,TypeError): continue
        if not fresh or item.get('score',0)<7 or not canonical_source(item.get('url','')): continue
        if not all(item.get(f'{field}_{lang}') for field in ('title','summary') for lang in ('ja','en')): continue
        if item.get('source') in sources: continue
        result.append(item);sources.add(item.get('source'))
        if len(result)==3: break
    return result

def render(items,lang):
    en=lang=='en'; chosen=picks(items)
    if not chosen: return ''
    rows=[]
    for n,item in enumerate(chosen,1):
        target=e(canonical_source(item['url']),quote=True)
        audience=item.get('useful_for_'+lang)
        rows.append(f'<article class="brief-item"><span class="brief-number">0{n}</span><div><p class="brief-meta">{e(item.get("source",""))} · {e(item["date"][:10])}</p><h3><a href="{target}" target="_blank" rel="noopener noreferrer" data-signal-event="source_click">{e(item["title_"+lang])}</a></h3><p>{e(item["summary_"+lang])}</p>'+ (f'<p class="brief-audience">{"For" if en else "関係する人"}：{e(audience)}</p>' if audience else '')+f'<a class="brief-source" href="{target}" target="_blank" rel="noopener noreferrer" data-signal-event="source_click">{"Read the source" if en else "出典で詳細を確認"} ↗</a></div></article>')
    title='Start with these changes' if en else 'まず押さえたい、直近の変化'
    desc='Up to 3 stories from the past 72 hours, selected by automated usefulness scores with varied sources. AI summaries from RSS excerpts.' if en else '過去72時間から有用度の自動評価をもとに最大3件。出典が偏らないよう選んでいます。RSS抜粋に基づくAI要約です。'
    return f'<section class="daily-brief" aria-labelledby="brief-title"><div class="brief-heading"><p class="kicker">THE SHORTLIST</p><h2 id="brief-title">{title}</h2><p>{desc}</p></div><div>{"".join(rows)}</div></section>'
