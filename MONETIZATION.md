# SIGNAL revenue implementation

## Strategy and current status

Existing news and AI-generated digests now lead to evergreen buying guides. The existing Amazon tag `tsukiproduct-22` is preserved in clearly labelled product-search links. No new account, payment plan, advertising contract, subscription or analytics vendor has been created. Amazon account approval and registration of the actual site URL must be checked by the owner; a tag in source alone does not establish eligibility or tracked earnings.

Added: video-production cost calculator, local-AI PC checklist, learning/book guide, advertising enquiry page using the existing contact email, disclosure page and sitemap. Prices, trial periods, sales rankings and untested product endorsements are deliberately not presented as verified facts. The calculator uses reader inputs and illustrative defaults, not vendor performance estimates.

Removed repetitive unrelated Prime/Kindle insertions and the nonfunctional newsletter form. Failed news loading now shows an error/retry instead of invented current headlines. The latest-digest hero now uses the actual JSON file key instead of the descriptive article ID.

## Activate an approved software partnership

Apply through the chosen provider and register the actual publishing URL. After approval, add a record to `docs/data/partners.json`:

```json
{
  "partners": [{
    "enabled": true,
    "guide": "video-budget",
    "name": "契約済みサービス名",
    "description": "公式情報で確認した、読者の用途に合う説明",
    "url": "https://provider.example/your-approved-link",
    "reviewed_on": "2026-09-08"
  }]
}
```

This is a schema example, not a real offer. Replace all example values with approved real information. Do not publish account secrets. Guide keys: `video-budget`, `local-ai`, `ai-learning`. Run `python3 scripts/configure_partners.py`, review the guide changes and commit both the config and rendered pages. Invalid enabled entries fail before writing pages. Disabled/deleted entries are removed on the next run. This is a manual publishing step; the existing news workflow is unchanged. Never let the digest LLM invent offers or affiliate URLs.

## Measurement

`assets/revenue.js` emits `signal:conversion` CustomEvents containing only event name, offer label, and page pathname. It does not send or retain data. Events: `guide_open`, `affiliate_click`, `sponsor_inquiry`. These are integration hooks, **not a functioning analytics dashboard**. Once an owner-selected analytics collector is configured, update the disclosure and connect a listener. Do not send calculator inputs or email contents.

Until then, use actual Amazon/partner reports for approved conversions and payouts; they cannot identify individual guide performance with the shared tag. Create separate tracking IDs in the affiliate account if per-guide attribution is desired; do not invent IDs. Report guide visits → outbound clicks → approved sales, excluding own test clicks and refunds. No traffic or revenue numbers have been verified in this change.

## Launch and editorial gates

- Review and merge the PR to publish through the repository's existing Pages setup. This change is not deployed separately.
- Confirm Amazon account/site approval. Configure only real approved software partnerships.
- Submit `/signal-news/sitemap.xml` in an owner-verified Search Console property. Do not add a project-directory robots.txt as if it controlled the domain root.
- Keep the news product and editorial value primary. GitHub Pages imposes restrictions on sites primarily facilitating commercial transactions; if the site becomes primarily commercial, review hosting suitability before publishing that expansion.
- Existing digests are AI-generated from collected material. This pass does not fact-check the archive. Do not bulk create/index derivative archive pages merely for search traffic; review facts and source fidelity before expanding SEO publication.
- Check selected offers monthly and after announced plan changes. Keep disclosures next to affiliate links.
- Revenue is not guaranteed. Start with traffic and conversion measurements before adding more guides or ads.

## Verified references (2026-09-08)

- Amazon disclosure: https://affiliate.amazon.co.jp/help/operating/agreement
- GitHub Pages limits: https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits
- Google spam policies: https://developers.google.com/search/docs/essentials/spam-policies
- Video plan sources: https://runway.com/pricing and https://www.adobe.com/products/firefly/plans.html
- Local AI requirements: https://lmstudio.ai/docs/app/system-requirements
