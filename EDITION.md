# SIGNAL practical bilingual edition

## Editorial direction

Audience: independent AI creators, developers, small teams. Rank usable releases,
workflow changes, costs and constraints above funding and event announcements.
The Opportunity Lab is explicitly untested editorial reasoning, not evidence of
demand, client experience or guaranteed income. No affiliate offer is invented.

## Build and update

`python3 scripts/build_edition.py` regenerates the Japanese root and `/en/`,
Opportunity Lab, sources pages, robots and sitemap. Edit the generator rather
than generated HTML. This relies on the custom-domain root `signal.tsukilab.jp`,
not the old `/signal-news/` project path. The existing CNAME on main must remain.

The existing three-times-daily workflow now runs the static build after curation.
Before merging, set Settings → Pages → Source to **GitHub Actions** (keep the
custom domain and HTTPS settings). The workflow explicitly uploads/deploys Pages
artifacts: a GITHUB_TOKEN bot commit alone does not trigger branch-based Pages.
Push to main builds/deploys without rerunning paid translation. Scheduled/manual
runs collect, translate, validate, commit and deploy. Deployment protection rules
remain in effect. No publication has been executed from this work session.
No deployment or new paid API account is created by this change.
Use `python3 scripts/test_edition.py` for offline regression checks.

News collection uses a 14-day freshness gate, explicit dates, AI-topic matching,
URL/title deduplication and a 60-candidate translation ceiling per update.
Unchanged successfully translated items are reused. The deterministic gate can
still miss relevant stories or include marginal ones; model scoring is a second
filter, not fact checking. Review editorial quality periodically.

Translation uses existing `ANTHROPIC_API_KEY` when set, otherwise existing
`OPENROUTER_API_KEY` with `openrouter/free`. The former can incur existing-account
charges; the latter is subject to availability/rate limits. Missing credentials
or API errors do not produce fabricated translations. Original-language fallback
is labelled. We have not verified repository secrets or executed paid calls here.
`translation_seed.json` provides initial RSS-based translations only; future
records are processed by the scheduled workflow. Buying guides have English
counterparts. Old Digest archives remain Japanese and are labelled as such.

## AEO / multilingual SEO

Core page content is static HTML. Japanese and English have separate URLs,
language attributes, self canonicals and reciprocal hreflang. Structured data
matches visible page content. No fake reviews, ratings, testing claims or FAQ
rich-result promises. No bulk per-news SEO pages are generated from RSS snippets.
`robots.txt` and sitemap are for the new custom-domain root.
Indexing, AI citations and revenue are not guaranteed.

Sources consulted:
- https://developers.google.com/search/docs/appearance/ai-features
- https://developers.google.com/search/docs/specialty/international/managing-multi-regional-sites
- https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum
- https://developers.cloudflare.com/fundamentals/new-features/available-rss-feeds/

## Measurement and limitations

No analytics provider has been connected. Existing `signal:conversion` events are
local hooks, not collected metrics. Saved stories and display settings remain
on the reader's device. Measure guide visits, disclosed affiliate outbound clicks
and approved conversions after the owner configures an analytics collector.
Do not claim increased traffic or revenue until measured.

Static parsing, local links, JS syntax, language fallback, deduplication and
calculator logic are checked offline. Browser rendering and accessibility have
not been certified; test real devices before declaring full WCAG conformance.
New RSS URLs were found through official publisher links; live parsing success
must be checked in the next Actions run. Respect publisher access/reuse terms.
