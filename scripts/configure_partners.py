#!/usr/bin/env python3
"""Render only explicitly enabled, owner-approved partner links. No API calls."""
import json
from html import escape
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
ALLOWED = {'video-budget', 'local-ai', 'ai-learning'}
START, END = '<!-- SIGNAL PARTNERS START -->', '<!-- SIGNAL PARTNERS END -->'

def render(entries):
    blocks = {slug: [] for slug in ALLOWED}
    for entry in entries:
        if entry.get('enabled') is not True:
            continue
        slug = entry.get('guide')
        url = urlparse(entry.get('url', ''))
        if slug not in ALLOWED or url.scheme != 'https' or not url.hostname or url.username or url.password:
            raise ValueError('Enabled partner must have an allowed guide and a public HTTPS URL without credentials')
        if not all(isinstance(entry.get(k), str) and entry[k].strip() for k in ('name', 'description', 'url', 'reviewed_on')):
            raise ValueError('Enabled partner requires name, description, URL and reviewed_on')
        from datetime import date
        date.fromisoformat(entry['reviewed_on'])
        blocks[slug].append('<section class="panel"><p class="pr">広告 / 提携サービス</p><h2>' + escape(entry['name']) + '</h2><p>' + escape(entry['description']) + '</p><a class="button" data-signal-event="affiliate_click" data-offer="' + escape(entry['name'], quote=True) + '" target="_blank" rel="sponsored noopener noreferrer" href="' + escape(entry['url'], quote=True) + '">公式サイトで条件を確認</a><p class="meta">掲載内容の確認日：' + escape(entry['reviewed_on']) + '。紹介リンクからの契約により運営者が報酬を受け取る場合があります。</p></section>')
    return blocks

def main():
    entries = json.loads((ROOT / 'docs/data/partners.json').read_text())['partners']
    blocks = render(entries)  # Validate every active record before writing any page.
    for slug, cards in blocks.items():
        page = ROOT / f'docs/guides/{slug}.html'
        text = page.read_text()
        if START not in text:
            text = text.replace('</main>', START + END + '</main>')
        a, b = text.index(START), text.index(END) + len(END)
        page.write_text(text[:a] + START + ''.join(cards) + END + text[b:])

if __name__ == '__main__':
    main()
