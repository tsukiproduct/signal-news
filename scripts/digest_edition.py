"""Rewrap the digest archive with the shared reader design on every build."""
import re


def build(docs, frame, origin):
    target = docs / 'digest.html'
    original = target.read_text()
    body = re.search(r'<!-- MAIN -->(.*?)<!-- FOOTER -->', original, re.S)[1].strip()
    script = re.search(r'<script>\s*(// ── CONFIG .*?)</script>', original, re.S)[1]
    if body.startswith('<div class="main-wrap">'):
        body = body.replace('<div class="main-wrap">', '<main id="main" class="wrap main-wrap">', 1)
        body = body.rsplit('</div>', 1)[0] + '</main>'
    body = body.replace('<h1>Digest</h1>', '<h1>まとめ読み</h1>')
    body = body.replace('Recent Digests', '最近のまとめ').replace('LOADING DIGEST…', 'まとめを読み込んでいます…')
    body = body.replace('<div class="back-btn" id="backBtn" onclick="showList()">← 記事一覧に戻る</div>', '<button type="button" class="back-btn" id="backBtn" onclick="showList()">← 記事一覧に戻る</button>')
    html = frame('ja', 'digest.html', 'AIニュースのまとめ読み', 'AIニュースをまとめて読み、出典と活用のヒントを確認できます。', '<!-- MAIN -->'+body+'<!-- FOOTER -->')
    html = html.replace('<link rel="alternate" hreflang="en" href="'+origin+'/en/digest.html">', '')
    html = html.replace('href="/en/digest.html" lang="en" hreflang="en" >English', 'href="/en/" lang="en" hreflang="en" >English news')
    html = html.replace('</head>', '<link rel="stylesheet" href="/assets/digest-reader.css"></head>')
    html = html.replace('</body>', '<script>\n'+script+'</script></body>')
    target.write_text(html)
