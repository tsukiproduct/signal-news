"""Check archive integration without changing archived article content."""
import re
import subprocess
import tempfile
from pathlib import Path
from build_edition import DOCS, ORIGIN, frame
from digest_edition import build

build(DOCS, frame, ORIGIN)
html = (DOCS/'digest.html').read_text()
build(DOCS, frame, ORIGIN)
assert html == (DOCS/'digest.html').read_text(), 'Build must be idempotent'
assert '/assets/reader.css' in html and '/assets/digest-reader.css' in html
assert 'logo-mark' not in html and '<style>' not in html
assert '/en/digest.html' not in html
assert 'https://buymeacoffee.com/tsuki_product' in html
for element in ('main','loadingState','digestList','digestCards','digestCount','articleReader','articleContent','backBtn','sidebar','sidebarDigests'):
    assert html.count('id="'+element+'"') == 1, element
for function in ('showList', 'openArticle', 'renderArticle', 'copyPrompt'):
    assert 'function '+function+'(' in html
with tempfile.NamedTemporaryFile(suffix='.js',mode='w') as script:
    script.write(re.search(r'<script>(.*?)</script>',html,re.S)[1]);script.flush()
    subprocess.run(['node','--check',script.name],check=True)
print('Digest: shared layout, routes, support, runtime syntax and repeat build passed.')
