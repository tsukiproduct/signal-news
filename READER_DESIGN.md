# Reader-first redesign

The user clarified that SIGNAL is for quick, useful AI news intake. Revenue is
the operator's goal, through disclosed advertising and voluntary support. The
previous Opportunity Lab and hourly-margin emphasis mixed those goals.

## Applied changes

- White background, graphite text, restrained dark red accents; serif masthead
  and Japanese system sans-serif for articles. This aesthetic is an editorial
  choice, not a claim that one palette universally improves readability.
- Desktop metadata column separates source/date from headline/summary; mobile
  uses a single column. No oversized promotional hero before the news.
- Search and topic filters remain accessible. Optional text size/theme controls
  are in a native disclosure, avoiding a dense wall of controls on phones.
- Main body approximately 16–17px; generous line-height; no fixed-height text
  boxes or truncation. Primary controls target 44px. Active topics have underline
  and weight changes, not color alone. Focus and reduced-motion rules remain.
- Buy Me a Coffee restored from the original site:
  https://buymeacoffee.com/tsuki_product . No new account or destination.
- Support follows the news and sits in the desktop sidebar/navigation. Ads and
  advertising enquiries are labelled separately. No popups or misleading links.
- Income experiment links removed from public navigation. Previous playbook
  URLs now contain a noindex retirement notice linking to news; removed from
  the sitemap. The historical proposal remains recoverable from Git history.
- Japanese buying guides share the new reading layout. Bilingual canonicals,
  hreflang, source links, static content and existing affiliate IDs are retained.
- Legacy Digest remains a separate Japanese archive; support restored in footer.

## Research used

- NN/g, text-scanning eye-tracking research:
  https://www.nngroup.com/articles/text-scanning-patterns-eyetracking/
  Use meaningful headings and visual hierarchy to help readers locate topics.
- W3C, text spacing:
  https://www.w3.org/WAI/WCAG21/Understanding/text-spacing
  Text containers must accommodate spacing overrides without clipping.
- W3C, resize text:
  https://www.w3.org/WAI/WCAG21/Understanding/resize-text
  Support text enlargement; do not make critical controls depend on tiny type.

## Validation and remaining limits

Offline checks cover generated routes, metadata, source escaping, support URL,
absence of operator-strategy links, syntax and existing calculator regressions.
Text/background token contrast was calculated for both themes. No real-device
or browser rendering test was performed, so this is not a WCAG certification.
Advertising conversion, donations and external discovery have not been measured.
This design change does not add an analytics collector or claim increased traffic.
