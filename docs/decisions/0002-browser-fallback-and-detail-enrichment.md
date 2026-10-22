# 0002 — Browser fallback and detail enrichment

**Problem.** About 23% of jobs arrive without a usable description, mostly from list APIs (Workday, getro) and board aggregators. Many have no reliable posted date either. Several popular job sites block plain HTTP clients with Cloudflare or similar.

**Options considered.**
1. Link out to the source and accept thin records.
2. Write a scraper per site for its detail page.
3. Use one generic detail parser based on schema.org `JobPosting` JSON-LD, which most job sites publish for Google Jobs, with a main-text fallback. Fetch over httpx and retry through a stealth browser (CloakBrowser) only when blocked.

**Decision.** Option 3.
- A new `enrich` source revisits thin jobs. New sites reuse the same parser through a config-driven listing collector.
- CloakBrowser runs on one dedicated thread, because Playwright's sync API is thread-bound and the free licence allows one session.
- The per-host 1 req/s throttle applies to browser fetches too.

**Consequences.**
- Adds Playwright and a ~200MB Chromium download on first browser use.
- Browser fetches are slower (~5–8s each) and serialised, so the browser is the fallback, not the default.
- Enrichment state lives on `jobs` (`enriched_at`, `enrich_status`); a failed job is retried after 7 days.
- The CloakBrowser binary licence: the free v146 binary is used. Newer builds need a key.
