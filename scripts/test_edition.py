"""Offline regression checks: language, links, structured data and input gates."""
import json
import unittest
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
from editorial import eligible, select, canonical_source
from build_edition import frame, card, localized, DOCS, home
from curate import merge_scores

class Document(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.scripts, self.lang, self.canonical, self.alternates = [], [], '', '', {}
        self.json_script = False
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'html': self.lang = a.get('lang')
        if a.get('href'): self.links.append(a['href'])
        if a.get('src'): self.links.append(a['src'])
        if tag == 'link' and a.get('rel') == 'canonical': self.canonical = a['href']
        if tag == 'link' and a.get('hreflang'): self.alternates[a['hreflang']] = a['href']
        if tag == 'script' and a.get('type') == 'application/ld+json': self.json_script = True
    def handle_endtag(self, tag):
        if tag == 'script': self.json_script = False
    def handle_data(self, data):
        if self.json_script: self.scripts.append(json.loads(data))

class EditionTests(unittest.TestCase):
    def item(self, **kw):
        return dict({'id':'test','title':'AI model update','summary':'A model update.','url':'https://example.com/story','date':datetime.now(timezone.utc).isoformat(),'lang':'en','category':'AI','score':5}, **kw)

    def test_generated_pages(self):
        for rel in ['index.html','en/index.html','playbook.html','en/playbook.html','sources.html','en/sources.html','en/guides.html','en/guides/video-budget.html','en/guides/local-ai.html','en/guides/ai-learning.html']:
            d = Document(); d.feed((DOCS/rel).read_text())
            self.assertEqual(d.lang, 'en' if rel.startswith('en/') else 'ja')
            self.assertEqual(set(d.alternates), {'ja','en','x-default'})
            self.assertTrue(d.canonical.startswith('https://signal.tsukilab.jp/'))
            self.assertTrue(d.scripts)
            for link in d.links:
                if link.startswith('/'):
                    target = DOCS / urlsplit(link).path.lstrip('/')
                    if target.is_dir(): target = target/'index.html'
                    self.assertTrue(target.exists(), f'{rel}: missing {link}')

    def test_topic_gates(self):
        self.assertTrue(eligible(self.item()))
        for changes in [{'category':'Events'}, {'title':'Plane crashes on runway','summary':''}, {'title':'Authors and agents','summary':''}, {'date':'nonsense'}, {'date':'2020-01-01T00:00:00+00:00'}]:
            self.assertFalse(eligible(self.item(**changes)))

    def test_url_and_duplicates(self):
        self.assertEqual(canonical_source('javascript:alert(1)'), '')
        self.assertEqual(canonical_source('https://[broken/path'), '')
        self.assertEqual(canonical_source('https://example.com/a?utm_source=x&q=1#hash'), 'https://example.com/a?q=1')
        self.assertEqual(len(select([self.item(), self.item(id='duplicate')])),1)

    def test_untranslated_is_not_japanese(self):
        item = self.item(summary_ja='Still English')
        self.assertEqual(localized(item,'summary','ja'), ('A model update.','en'))
        self.assertIn('日本語訳は準備中',card(item,'ja'))

    def test_escaping(self):
        body = card(self.item(title='<img src=x onerror=alert(1)>',summary='</p><script>bad()</script>'),'ja')
        self.assertNotIn('<img',body)
        self.assertNotIn('<script>',body)

    def test_scoring_validation(self):
        result = merge_scores([self.item()],[{'id':'test','score':'bad','title_ja':'AI更新','title_en':'AI update','summary_ja':'更新情報','summary_en':'Update'}])[0]
        self.assertEqual(result['score'],5)
        self.assertEqual(result['translation_status'],'machine')

    def test_empty_static_edition(self):
        self.assertIn('No matching stories',home('en',{'items':[],'updated_at':''}))

    def test_reader_focus_and_existing_support(self):
        for rel in ('index.html','en/index.html','guides.html','en/guides.html'):
            content = (DOCS/rel).read_text()
            self.assertIn('https://buymeacoffee.com/tsuki_product', content)
            self.assertIn('/assets/reader.css', content)
            self.assertNotIn('href="/playbook.html',content)
            self.assertNotIn('href="/en/playbook.html',content)
            self.assertNotIn('Opportunity lab',content)
            self.assertNotIn('小さく稼ぐ実験室',content)
        self.assertNotIn('playbook.html',(DOCS/'sitemap.xml').read_text())
        self.assertIn('noindex,follow',(DOCS/'playbook.html').read_text())

if __name__ == '__main__': unittest.main()
