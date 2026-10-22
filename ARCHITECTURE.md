# Job Radar — Architecture

Local aggregator for crypto job postings. It polls company hiring systems (ATS), crypto job boards and popular general job sites in many languages, removes duplicates, fills in full job details, and serves a browsable UI at http://127.0.0.1:8765. It runs on one Mac with no cloud. The only LLM is DeepSeek, called with the key David loads in Settings (docs/decisions/0005).

## Flow
collectors → `Posting` → `ingest` (dedup) → SQLite → `enrich` (job pages) → FastAPI + Jinja + htmx UI

`runner` picks the sources that are due (each source has its own interval) and holds a poll lock. launchd starts it every 15 minutes. `enrich` runs last in a poll.

**Fetching.** `Http` throttles to 1 req/s per host (LinkedIn 6 s). `Http.html()` tries httpx and, on a block (401/403/429/503 or a challenge page), renders the URL through CloakBrowser. The browser runs on one dedicated thread: Playwright's sync API is thread-bound and the free licence allows one session. See docs/decisions/0002.

**Job pages.** `detail.parse()` reads the schema.org `JobPosting` JSON-LD most job sites publish, then known description containers (LinkedIn), then trafilatura main text.

## Data model (SQLite, data/jobradar.db)
- **companies** — one row per normalised company key. Aliases are applied, e.g. Payward → Kraken. `sector` (crypto / other) drives the default "Crypto companies" view; `sector_source` records which rule set it.
- **boards** — ATS boards to poll. Seeded from seeds/boards.csv and auto-discovered from aggregator URLs (case-insensitive). `crypto_only` boards (DBS, Crusoe, DRW, Robinhood) keep only crypto-titled roles.
- **jobs** — canonical jobs. The description prefers the ATS copy, then the longest job-page copy. `lang` is detected from title + description; `enriched_at` / `enrich_status` record the last job-page fetch. `role`, `seniority`, `countries` (ISO-2 list) and `remote_scope` (anywhere / restricted) come from classify.py.
- **sightings** — every (source, source_job_id) where a job was seen.
  - kind = source family (ats, getro, telegram, seek, …)
  - match = exact | probable
  - detail_url = the page to fetch for full details, when it differs from the apply link (getro, LinkedIn, Wanted)
- **skipped** — job links a site collector fetched and rejected as not crypto, so they are not fetched again.
- **source_runs** — one row per source run: status, counts, error.
- **jobs_fts** — FTS5 trigram index over title, company and description.
- **match_evaluations** — job-fit scores, one row per job, shown on `/shortlist`. Each row has:
  - `run`, `verdict` (apply_now / tailor_then_apply / stretch / skip) and `track`;
  - scores `rec`, `hm` and `want`, plus `priority` = rec·hm·want/10000;
  - `why`, `risk` and `start_cv`;
  - David's `label` (Y/M/N), `label_note` and `labelled_at`.

  An import updates the scores and never touches the label fields (docs/decisions/0004).
- **preferences** — David's job preferences as versioned JSON (the newest row is current). The fields and allowed values are defined in `prefs.SCHEMA`; the default focus is data analyst.
- **pref_messages** — the preferences chat. An assistant message may carry a `proposal` (validated changes) with `status` pending / applied / discarded. A `divider` row starts a new conversation.

## Shortlist (match.py, /shortlist)
- **Where the scores come from:** `python -m jobradar match import FILE.json` loads evaluations. For now these are hand-scored runs from job_related/docs/runs/; later the LLM matcher writes through the same `import_results()`.
- **The page:** jobs are grouped by verdict and sorted by priority, with "Unlabelled only" and verdict filters. Clicking a title opens the full ad in the detail pane.
- **Labelling:** Y / M / N plus a note are saved through htmx (`POST /shortlist/{job_id}/label`). The nav tab shows how many jobs are still unlabelled.

## DeepSeek, Settings and Preferences (keystore.py, deepseek.py, prefs.py)
- **Key.** `/settings` saves the DeepSeek key in the macOS Keychain (`keystore.py`, service `jobradar.deepseek`) only after the free `GET /user/balance` check passes. The `DEEPSEEK_API_KEY` environment variable overrides the Keychain. The database never holds the key.
- **Client.** `deepseek.py` makes plain httpx calls: `balance()`, and `chat_json()`, which uses JSON mode with thinking off by default. It retries once on a dropped connection or a reply that isn't a JSON object, and logs every call (model, seconds, tokens, finish reason) and every failure.
- **Logs.** `jobradar serve` logs at INFO to stderr, which goes to `data/web.log` (under launchd, or when started by hand with that redirect). A failed chat turn logs its traceback and the first 300 characters of David's message, and the page keeps the typed text so it can be resent.
- **Preferences chat.** `/preferences` shows what the matcher knows next to a chat with `deepseek-flash`. Each turn sends:
  - the system prompt from `seeds/prefs_assistant_prompt.md`;
  - the field list;
  - the current preferences;
  - what is still unset;
  - the last 20 messages.

  DeepSeek returns `{"reply", "changes"}`. The changes are validated and shown as a proposal card, and **Apply** saves a new preferences version, which updates the summary through an htmx out-of-band swap. With an empty conversation, the page asks DeepSeek for an opening question about the first unset item.

## Dedup ladder (ingest.py)
1. Same (source, source_job_id): a re-sighting of a known job.
2. Same ATS job id (gh:/lever:/ashby:/workable:): the same job.
3. Same company + normalised title, last seen within 45 days:
   1. same URL (including its query string): the same job.
   2. description similarity ≥ 0.85: the same job (catches per-city copies).
   3. one side has no description: attach as *probable*.
   4. otherwise: a different job.
4. Otherwise: a new job.

The evidence for these thresholds is in job_related/docs/research/2026-10-21-job-monitor-research.md §6.

## Freshness and dates
Every source is fully re-pulled each run. Jobs not seen for 10 days are "stale" and hidden by default.

The "posted" filter uses `posted_at` only. A new job without a date gets `posted_at = now` only if its source (or ATS board) had a successful run before, i.e. it genuinely just appeared; jobs from a source's first backfill stay undated until `enrich` finds a date on the job page. Undated jobs show "date unknown" and sort last.

## Enrichment (enrich.py)
Each run takes up to 400 active jobs that have no description, one under 200 characters, or no date, and that were not tried in the last 7 days. For each job it tries up to three URLs (detail_url, apply link, other sightings) on 8 threads. A result is accepted only if its title shares at least half the job title's words, so a redirect to a generic careers page is not stored.

## Classification (classify.py)
- **Company sector.** Recomputed at the end of every poll. Rules in order, first match wins:
  1. Override in seeds/company_sectors.csv, or set with the toggle on the Companies page, which appends to that file.
  2. A `crypto_only` board → other.
  3. A crypto word in the company name → crypto.
  4. At least 40% of its jobs use a strong crypto term (`is_web3`) → crypto.
  5. A seed board plus some evidence: fewer than 5 jobs, any strong term, or 20% of jobs using two or more weak terms (protocol, network, token, wallet…) → crypto.
  6. Seen on a crypto board, with at least 20% strong terms → crypto.
  7. Otherwise → other.

  Neither the source nor the job text is enough on its own (see docs/decisions/0003). The 479 companies with 5+ jobs, and the small companies seen on crypto boards, were reviewed by hand on 2026-10-22.
- **Job fields.** Set on create, merge and enrichment:
  - role: 15 families, from an ordered title regex in several languages.
  - seniority: from title words; mid when none match.
  - countries: place words, plus a trailing ISO or US-state code.
  - remote_scope: anywhere unless a country or region is named.

## Layout
- **src/jobradar/** — config, models, normalize, db, http, browser, detail, enrich, lang, ingest, registry, runner, match, keystore, deepseek, prefs, `__main__`
- **src/jobradar/collectors/** — ats.py (14 ATS adapters), one module per crypto aggregator, seek.py, linkedin.py, boards.py (small API/RSS boards) and sites.py (config-driven listing → job page collector for Habr, hh.ru, DOU, Djinni, Just Join IT, No Fluff Jobs, Green, Rocketpunch, Cutshort, ITviec, remote3, Foresight, 登链社区)
- **src/jobradar/web/** — app.py, queries.py, templates/, static/
- **seeds/boards.csv** — research seed of about 640 boards
- **seeds/prefs_assistant_prompt.md** — the preferences assistant's instructions
- **tests/** — pytest. tests/fixtures holds recorded real responses (made by scripts/record_fixtures.py).

## Running
python -m jobradar seed | poll [--source NAME] [--force] | relang | reclassify | match import FILE [--run NAME] | serve [--port N]

`seed` also loads seeds/company_sectors.csv. `reclassify` recomputes every job's fields and every company's sector.

- **First time:** `seed`, then `poll --force`, then `serve`. A full poll takes about 8 minutes. Aggregators are fetched in background threads while the ATS pass runs with 8 workers; the 1 req/s per-host limit still holds, so getro (22 networks on one API host, ~7.5 min) sets the floor. The ATS pass took 4 min for ~9.8k jobs on 2026-10-21. Each ATS board is committed as it lands, so the UI fills in during the run. All SQLite writes stay on the main thread.
- **Scheduling:** launchd/com.davidc.jobradar.poll.plist runs `poll` every 15 minutes, and each source decides whether it is due. launchd/com.davidc.jobradar.web.plist keeps the UI running.

  Install:
  `cp launchd/*.plist ~/Library/LaunchAgents/ && launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.davidc.jobradar.poll.plist` (same for `.web`).

  Stop:
  `launchctl bootout gui/$(id -u)/com.davidc.jobradar.poll`.
- **Rebuild from scratch:** `rm data/jobradar.db && python -m jobradar seed && python -m jobradar poll --force`.
- **Logs:** data/poll.log and data/web.log (launchd); data/first-poll.log (manual first run).

## Operating notes (first poll, 2026-10-21)
- 23,686 sightings → 10,263 jobs (43% merged). 684 sightings attached as *probable*.
- The same job often appears on many getro networks (one Ripple role had 23 sightings), so getro adds many sightings but few new jobs.
- 69 seed boards returned 404 and are disabled in seeds/boards.csv with origin suffix `+404`. Check the Failing boards table on /sources after each full poll.
- eleduck can legitimately return 0: it is a general remote-work feed filtered to web3 keywords.
- UI opens on "posted in last 7 days"; pick "any time" to see everything.

## Operating notes (v2 backfill, 2026-10-22)
- The date fix took the 7-day view from 2,050 jobs to 881. After the new sources landed it shows 1,582.
- The enrich backlog (~2,700 jobs) cleared in 7 runs. A 400-job run took 27 min with the old fixed 4 s browser wait, then 5–14 min after the wait was cut to 1.5 s.
- Afterwards, of 12,078 active jobs: 96.8% have a full description, 99.5% are dated, and none are still waiting for a first enrich attempt. Of the attempts, 2,508 were ok, 140 returned some other page, 44 errored (mostly 404s on dead job links) and 4 were too short to use.
- LinkedIn's guest API starts rate-limiting after about 12 quick calls, which is why it has a 6 s host interval.

## Adding a source
- **A site whose job pages carry JSON-LD:** add a `Site` entry in collectors/sites.py (listing URLs, job-link regex, detail URL format, `browser=True` if it blocks httpx, `crypto_only=True` if its search is fuzzy) and an interval in config.INTERVALS.
- **An API or feed:** write `collect(http) -> list[Posting]`, register it in collectors/__init__.py and config.INTERVALS, record a fixture (`scripts/record_fixtures.py NAME`) and add a test.

Not added (2026-10-22): Indeed, StepStone and Glassdoor (still blocked through CloakBrowser), BOSS直聘 (login wall), Naukri (mostly noise), Wellfound (stale role pages), Welcome to the Jungle (Algolia keys not yet found), BeInCrypto (no job links), useweb3 (closed).

Major crypto employers without a usable careers feed (2026-10-22): KuCoin, HTX, MEXC, Bitget, Upbit/Dunamu, OSL, Matrixport/BIT, Messari, Arkham, Glassnode and Kaiko. Their careers pages are JavaScript apps on custom backends; HashKey's WordPress API returns no job data. Their jobs still arrive through LinkedIn, getro and jobstash where posted. bitFlyer is collected from its Jobcan pages (sites.py).
