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

## Adding a source
1. Write `collect(http) -> list[Posting]`.
2. Register it in collectors/__init__.py and config.INTERVALS.
3. Record a fixture and add a test.
