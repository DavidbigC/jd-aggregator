# Job Radar — Architecture

Local aggregator for crypto job postings. It polls company hiring systems (ATS), crypto job boards and popular general job sites in many languages, removes duplicates, fills in full job details, and serves a browsable UI at http://127.0.0.1:8765. It runs on one Mac, with no cloud and no LLM yet.

## Flow
collectors → `Posting` → `ingest` (dedup) → SQLite → `enrich` (job pages) → FastAPI + Jinja + htmx UI

`runner` picks the sources that are due (each source has its own interval) and holds a poll lock. launchd starts it every 15 minutes. `enrich` runs last in a poll.

**Fetching.** `Http` throttles to 1 req/s per host (LinkedIn 6 s). `Http.html()` tries httpx and, on a block (401/403/429/503 or a challenge page), renders the URL through CloakBrowser. The browser runs on one dedicated thread: Playwright's sync API is thread-bound and the free licence allows one session. See docs/decisions/0002.

**Job pages.** `detail.parse()` reads the schema.org `JobPosting` JSON-LD most job sites publish, then known description containers (LinkedIn), then trafilatura main text.

## Data model (SQLite, data/jobradar.db)
- **companies** — one row per normalised company key. Aliases are applied, e.g. Payward → Kraken.
- **boards** — ATS boards to poll. Seeded from seeds/boards.csv and auto-discovered from aggregator URLs (case-insensitive). `crypto_only` boards (DBS, Crusoe, DRW, Robinhood) keep only crypto-titled roles.
- **jobs** — canonical jobs. The description prefers the ATS copy, then the longest job-page copy. `lang` is detected from title + description; `enriched_at` / `enrich_status` record the last job-page fetch.
- **sightings** — every (source, source_job_id) where a job was seen.
  - kind = source family (ats, getro, telegram, seek, …)
  - match = exact | probable
  - detail_url = the page to fetch for full details, when it differs from the apply link (getro, LinkedIn, Wanted)
- **skipped** — job links a site collector fetched and rejected as not crypto, so they are not fetched again.
- **source_runs** — one row per source run: status, counts, error.
- **jobs_fts** — FTS5 trigram index over title, company and description.

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

## Layout
- **src/jobradar/** — config, models, normalize, db, http, browser, detail, enrich, lang, ingest, registry, runner, `__main__`
- **src/jobradar/collectors/** — ats.py (14 ATS adapters), one module per crypto aggregator, seek.py, linkedin.py, boards.py (small API/RSS boards) and sites.py (config-driven listing → job page collector for Habr, hh.ru, DOU, Djinni, Just Join IT, No Fluff Jobs, Green, Rocketpunch, Cutshort, ITviec, remote3, Foresight, 登链社区)
- **src/jobradar/web/** — app.py, queries.py, templates/, static/
- **seeds/boards.csv** — research seed of about 640 boards
- **tests/** — pytest. tests/fixtures holds recorded real responses (made by scripts/record_fixtures.py).

## Running
python -m jobradar seed | poll [--source NAME] [--force] | relang | serve [--port N]

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

## Adding a source
- **A site whose job pages carry JSON-LD:** add a `Site` entry in collectors/sites.py (listing URLs, job-link regex, detail URL format, `browser=True` if it blocks httpx, `crypto_only=True` if its search is fuzzy) and an interval in config.INTERVALS.
- **An API or feed:** write `collect(http) -> list[Posting]`, register it in collectors/__init__.py and config.INTERVALS, record a fixture (`scripts/record_fixtures.py NAME`) and add a test.

Not added (2026-10-22): Indeed, StepStone and Glassdoor (still blocked through CloakBrowser), BOSS直聘 (login wall), Naukri (mostly noise), Wellfound (stale role pages), Welcome to the Jungle (Algolia keys not yet found), BeInCrypto (no job links), useweb3 (closed).
