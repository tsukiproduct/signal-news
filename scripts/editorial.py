"""Deterministic eligibility gates shared by collection and rendering."""
import re
from datetime import datetime, timezone, timedelta
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

AI_TERMS = re.compile(r"\b(ai|llm|gpt|claude|gemini|copilot|ollama|agentic|hugging\s*face)\b|artificial intelligence|machine learning|stable diffusion|人工知能|生成AI|機械学習|画像生成|動画生成|プロンプト|大規模言語|midjourney|comfyui", re.I)

def eligible(item, now=None):
    if item.get('source') in {'Bloomberg Tech', 'NHK テクノロジー'}:
        return False
    if item.get('category') == 'Events':
        return False
    if not AI_TERMS.search(item.get('title', '') + ' ' + item.get('summary', '')):
        return False
    try:
        date = datetime.fromisoformat(item['date'].replace('Z', '+00:00'))
        now = now or datetime.now(timezone.utc)
        return now - timedelta(days=14) <= date <= now + timedelta(hours=1)
    except (KeyError, ValueError, TypeError):
        return False

def canonical_source(url):
    try:
        parsed = urlsplit(url)
        _ = parsed.port
    except (ValueError, TypeError):
        return ''
    if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username:
        return ''
    query = urlencode([(k, v) for k, v in parse_qsl(parsed.query) if not k.startswith('utm_') and k not in ('fbclid', 'gclid')])
    return urlunsplit((parsed.scheme, parsed.netloc.lower(), parsed.path, query, ''))

def select(items, limit=60):
    seen, result = set(), []
    for item in sorted(items, key=lambda x: (x.get('score', 5), x.get('date', '')), reverse=True):
        url = canonical_source(item.get('url', ''))
        key = re.sub(r'\W+', '', item.get('title', '').casefold())
        if not url or not eligible(item) or url in seen or key in seen:
            continue
        seen.update((url, key))
        result.append(item)
    return result[:limit]
