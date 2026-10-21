# Job Radar — Architecture

Local aggregator for crypto job postings. It polls company hiring systems (ATS) and crypto job boards, removes duplicates, and serves a browsable UI at http://127.0.0.1:8765. It runs on one Mac, with no cloud and no LLM yet.

## Flow
collectors → `Posting` → `ingest` (dedup) → SQLite → FastAPI + Jinja + htmx UI

`runner` picks the sources that are due (each source has its own interval) and holds a poll lock. launchd starts it every 15 minutes.

## Data model (SQLite, data/jobradar.db)
- **companies** — one row per normalised company key. Aliases are applied, e.g. Payward → Kraken.
- **boards** — ATS boards to poll. Seeded from seeds/boards.csv and auto-discovered from aggregator URLs.
- **jobs** — canonical jobs. The description prefers the ATS copy.
- **sightings** — every (source, source_job_id) where a job was seen.
  - kind = source family (ats, getro, telegram, …)
  - match = exact | probable
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

## Freshness
Every source is fully re-pulled each run. Jobs not seen for 10 days are "stale" and hidden by default.

## Layout
- **src/jobradar/** — config, models, normalize, db, http, ingest, registry, runner, `__main__`
- **src/jobradar/collectors/** — ats.py (14 ATS adapters) plus one module per aggregator
- **src/jobradar/web/** — app.py, queries.py, templates/, static/
- **seeds/boards.csv** — research seed of about 640 boards
- **tests/** — pytest. tests/fixtures holds recorded real responses (made by scripts/record_fixtures.py).

## Running
python -m jobradar seed | poll [--source NAME] [--force] | serve [--port N]

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
1. Write `collect(http) -> list[Posting]`.
2. Register it in collectors/__init__.py and config.INTERVALS.
3. Record a fixture and add a test.
