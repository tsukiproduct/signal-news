# Reader briefing experience

The news homepage now opens with a maximum of three recent, translated stories (within 72 hours, score >= 7, varied sources). No fallback to old headlines when no eligible stories exist. Dates and RSS/AI basis remain visible. Main feed remains searchable and paginated, with newest-first default.

Audience and caveats are visible without expanding each news card. Subsequent curation leads with actual changes and prioritizes pricing, quotas, availability, licenses and capabilities. Existing summaries are not retroactively fabricated or relabelled as newly verified. Digest generation receives a 1600-character target and instructions to omit unsupported sections.

A previous-visit timestamp stays in local storage. Returning readers can filter by publication date after that timestamp. This is device-local convenience, not an operator analytics dashboard. Storage-denied browsers remain usable.

Source links dispatch source_click through the existing signal:conversion hook; affiliate, support and guide events already exist. No remote collector is configured. Actual traffic, retention and conversion measurement still requires an analytics service/site identifier. Do not describe local preferences or dispatched events as aggregate analytics.

Advertising remains visibly labelled; existing Kindle Unlimited and Buy Me a Coffee links remain. Reader brief selection does not depend on advertiser payments.

Validation: bounded/fresh/diverse brief selection, empty fallback, escaping, static page integration, pagination and blocked storage. Browser rendering and live analytics are not verified.
