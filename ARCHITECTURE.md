# JD Aggregator — Architecture

Formerly Job Radar (renamed 2026-10-23).

Local aggregator for crypto job postings. It polls company hiring systems (ATS), crypto job boards and popular general job sites in many languages, removes duplicates, fills in full job details, and serves a browsable UI at http://127.0.0.1:8765. It runs on one Mac with no cloud. The app calls no LLM. Claude, working in Claude Code, scores jobs and writes CVs through CLI hand-offs, and the app's code checks the results (docs/decisions/0008).

## Flow
collectors → `Posting` → `ingest` (dedup) → SQLite → `enrich` (job pages) → FastAPI + Jinja + htmx UI

`runner` picks the sources that are due (each source has its own interval) and holds a poll lock. launchd starts it every 15 minutes. `enrich` runs last in a poll.

**Fetching.** `Http` throttles to 1 req/s per host (LinkedIn 6 s). `Http.html()` tries httpx and, on a block (401/403/429/503 or a challenge page), renders the URL through CloakBrowser. The browser runs on one dedicated thread: Playwright's sync API is thread-bound and the free licence allows one session. See docs/decisions/0002.

**Job pages.** `detail.parse()` reads the schema.org `JobPosting` JSON-LD most job sites publish, then known description containers (LinkedIn), then trafilatura main text.

## Data model (SQLite, data/jd_aggregator.db)
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
  - `run`, `verdict` (apply_now / tailor_then_apply / stretch / needs_ad / skip), `reason` (why a skip) and `track`;
  - scores `rec`, `hm` and `want`, plus `priority` = want^0.5 · hm^0.35 · rec^0.15 (Want counts most; docs/decisions/0007);
  - `why`, `risk` and `start_cv` (the closest earlier application CV);
  - stamps `model`, `prompt_version`, `profile_hash`, `prefs_version` and `description_hash`, and `result`, the matcher's full validated JSON. Hand-scored rows have no `model`;
  - David's `label` (Y/M/N), `label_note` and `labelled_at`.

  An import updates the scores and never touches the label fields (docs/decisions/0004).
- **preferences** — David's job preferences as versioned JSON (the newest row is current). The fields and allowed values are defined in `prefs.SCHEMA`; the default focus is data analyst.
- **match_runs** — one row per `match results` load: model, preferences version, answers given, saved and refused. The token and cost columns are from the DeepSeek runs.
- **pref_messages** — the old DeepSeek preferences chat; kept, no longer written.
- **tailored_cvs** — one row per tailored CV attempt (the newest per job is shown, older rows are kept):
  - `status` (running / done / error) and `stage` (queued / writing / reviewing / revising / checking);
  - stamps `model`, `prompt_version` (both CV prompts) and `sources_hash` (the source pack);
  - the `draft`, `review` (of the draft), `final` and `final_review` JSON;
  - `score` (the final screen's; older rows: the draft review's), `cost_usd` and `error`.
- **settings** — small local key/value settings. `cv_contact` is the CV contact line; it is added only when a CV is rendered.

## Matcher and Shortlist (match/, /shortlist)
Claude scores the jobs; the code decides the verdict. See docs/decisions/0008.
- **Prefilter** (`match/prefilter.py`, free). Active crypto jobs → posted within `fresh_days` → title fits (keep and drop rules, widened or narrowed by `analyst_types` and `other_tracks`; compliance stays out unless David says yes or maybe) → location fits → ad language → one job per company and normalised title. Location: remote-anywhere (or 5+ "Remote (XX)" entries) and unspecified remote always pass; region-limited remote passes when its region is in `remote_regions` (UK and Europe until David sets it), with `single_country_remote` applied; offices only with `remote_or_uk_office`. The page shows the count after each step.
- **Scoring** (`match/runner.py`, `match/evaluate.py`). `python -m jd_aggregator match todo FILE` runs the prefilter and writes the jobs that need scoring, with the preferences, as JSON. A thin ad (under 500 characters) first gets one fetch from its sighting URLs; if it is still thin it is saved as `needs_ad` and left out. Claude reads `seeds/candidate_profile.md` and `seeds/match_prompt.md`, answers each job in the prompt's output shape plus `job_id`, and loads the answers with `match results FILE`. `clean()` validates each answer (scores clamped to 0–100, unquoted knockouts dropped, unknown CVs dropped) and an unusable one is refused and listed. Knockouts are eligibility only: `right_to_work`, `location`, `language`, `licence`. Any other type (years, skills) becomes a "Hard ask" top risk instead, so a skill gap can't hide a job. `apply_notes` (code words, details to include) show as a "To apply" line on the shortlist row. `verdict()` applies the rules in order, led by Want (docs/decisions/0007): knockout or not actually remote → skip; want < 45 → skip; backend/quant → stretch if hm ≥ 40, else skip; apply now (want ≥ 65, hm ≥ 60, rec ≥ 50); tailor then apply (want ≥ 55 and hm ≥ 45, or rec ≥ 45 and hm ≥ 50); stretch (want ≥ 55, hm ≥ 35); else skip. `match rescore` re-derives every verdict and priority from the stored scores.
- **Re-scoring.** A job is scored again only when it has no scored row, or its ad, the profile, the prompt, the model (`claude-opus-5-5`) or the preferences version changed. `/shortlist` shows how many are waiting and the last load.
- **The page.** Grouped by verdict and sorted by priority, with Unlabelled, verdict and track filters. At most 3 jobs per company per group; the rest sit under "more from companies already listed". Each row shows the scores, why, watch-outs, the base CV, "Matcher notes" (must-haves met or not, what to lead with, keywords, interview prep, questions for the recruiter) and who scored it. The header line shows how many of David's labels the matcher agrees with (Yes/Maybe vs a shown verdict, No vs skip).
- **Labelling:** Y / M / N plus a note are saved through htmx (`POST /shortlist/{job_id}/label`). Re-scoring never touches labels. The nav tab counts unlabelled jobs with a shown verdict.
- **Hand-scored runs** still load with `python -m jd_aggregator match import FILE.json`, through the same `import_results()`.
- **Profile review.** The Preferences page shows the candidate profile; corrections go into `profile_notes` (through `prefs set`) and win over the profile.

## Tailored CVs (cv/, docs/decisions/0006)
Every job pane, on Jobs and on Shortlist, has a **Tailored CV** section. Claude writes it from the audited master CV, reviews it as the screening recruiter, and the code checks it.
- **Source pack** (`cv/sources.py`). `python -m jd_aggregator cv sources` builds `seeds/cv_sources.md` from devmaster-cv (`CV_SOURCE_DIR`, default `~/job_related/devmaster-cv`, or `JD_AGGREGATOR_CV_DIR`): the README, experience, skills and every project file. While building it:
  - dollar amounts are cut, except the "$1M volume" ranking threshold. A bracketed or comma-separated fragment with an amount is removed; otherwise the line is dropped;
  - email and phone lines are dropped;
  - the README's PDF and repo-upkeep sections are dropped.

  The Ultra CV Master is never used. Rebuild the pack after editing devmaster-cv; CVs made from an older pack show "made from an older master CV".
- **Writing** (`cv/runner.py`). `python -m jd_aggregator cv todo FILE` lists the shortlisted jobs (shown verdicts, best first) whose CV is missing or was made with an older model, prompt or pack, each with the job message: the ad plus the matcher's must-haves, lead_with, keywords, risks and apply notes. For each, Claude:
  1. writes the CV from `seeds/cv_sources.md` following `seeds/cv_writer_prompt.md` (the goal: make the screening recruiter want to call David, within the truth rules);
  2. reviews it with `seeds/cv_review_prompt.md`, as the in-house recruiter screening 200 applications: a score (any invented claim caps it at 40), issues (must_fix / should_fix), missing keywords and invented claims;
  3. revises it and screens the final the same way.

  `cv save FILE` takes `{job_id, final, final_review, draft?, review?}` (one or a list). The final screen's score is stored in `tailored_cvs.score` and shown; its issues show as "Still weak", and invented claims show up front as "Check before sending". A missing draft or review defaults to the final.
- **Checks in code.** `clean_cv()` caps lengths and strips Markdown. `problems()` refuses a CV at `cv save` that has an email, a phone number, a dollar amount, he/she or 他/她, "merged" PRs, a hedge ("not merged", "team result", "exposure to", 团队成果), "trader" in the headline or a title, FLOKI shown as current, a skill item longer than 5 words outside brackets, the same figure in two experience/project/highlight places (the summary may repeat), more than 950 words (1,800 CJK characters), "5+ years" when the ad asks for more, or no Independent, FLOKI or Dragon Race role. `clean_cv()` also turns "Independent | Independent On-Chain…" headings into the title alone. A refused CV is listed with the reasons, fixed and saved again.
- **Rendering.** The app renders the final JSON itself, in the devmaster-cv layout:
  - name;
  - headline;
  - the Settings contact line plus the public links from the pack;
  - Summary, Core Skills, Experience (`Org | Title | Dates`), Selected Projects, Additional Highlights, Education. Chinese CVs get Chinese headings.

  `/jobs/{id}/cv` is the print page, styled with `static/resume.css` (a copy of devmaster-cv's). Its title, "David Chen - Company Title", becomes the PDF file name in Save as PDF. The job pane shows it in an iframe (`?embed=1`), plus **Download PDF**, **Copy as Markdown** (the same layout, ready for md-to-pdf).

- **PDFs** (`cv/pdf.py`). Each finished CV is saved to `CV_PDF_DIR`, which defaults to `~/Documents/JD Aggregator CVs/` and can be overridden with the `JD_AGGREGATOR_CVS` env var, as "David Chen - Company Title.pdf". A rewrite overwrites the file.
  - `pdf.html()` renders `cv_print.html` with `resume.css` inlined. `pdf.render()` prints it through Playwright's headless Chromium (A4, the CSS `@page` margins). Install that browser once with `python -m playwright install chromium-headless-shell`. It is separate from CloakBrowser, whose free licence allows a single session.
  - `runner.save` saves the PDF as a CV is stored. A failure is logged, and the CV still counts as done.
  - `GET /jobs/{id}/cv.pdf` re-renders, so a changed contact line is picked up, then saves the file and downloads it.
  - `POST /jobs/{id}/cv/reveal` and `POST /cvs/folder` run `open -R` / `open`. This works because the app runs locally.
  - The job pane shows the saved path, and the shortlist CV panel shows the folder.
  - `cv pdfs` writes the PDFs for every finished CV.
  - Tests use a temporary folder and a stub renderer, through an autouse fixture in conftest. One test renders with real Chromium.

## Settings and Preferences (keystore.py, deepseek.py, prefs.py)
- **DeepSeek key.** Not used for any LLM work since 2026-10-24, kept in case David switches back. `/settings` saves it in the macOS Keychain (`keystore.py`, service `jd-aggregator.deepseek`) only after the free `GET /user/balance` check (`deepseek.balance()`, the module's only call) passes. The `DEEPSEEK_API_KEY` environment variable overrides the Keychain. The database never holds the key.
- **CV contact line.** `/settings` also saves the line shown under David's name on tailored CVs, in the `settings` table. It is added only when rendering.
- **Logs.** `jd_aggregator serve` logs at INFO to stderr, which goes to `data/web.log` (under launchd, or when started by hand with that redirect).
- **Preferences.** `/preferences` shows what the matcher knows, read-only, with the candidate profile. David tells Claude what to change; `python -m jd_aggregator prefs set FILE` validates the JSON changes against `prefs.SCHEMA` (unknown keys and disallowed values dropped, maps merged, lists replaced) and saves a new preferences version, which makes the changed jobs due for re-scoring.

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
- **src/jd_aggregator/** — config, models, normalize, db, http, browser, detail, enrich, lang, ingest, registry, runner, match/ (prefilter, evaluate, runner), cv/ (sources, tailor, runner, pdf), keystore, deepseek, prefs, `__main__`
- **src/jd_aggregator/collectors/** — ats.py (14 ATS adapters), one module per crypto aggregator, seek.py, linkedin.py, boards.py (small API/RSS boards) and sites.py (config-driven listing → job page collector for Habr, hh.ru, DOU, Djinni, Just Join IT, No Fluff Jobs, Green, Rocketpunch, Cutshort, ITviec, remote3, Foresight, 登链社区)
- **src/jd_aggregator/web/** — app.py, queries.py, templates/, static/
- **seeds/boards.csv** — research seed of about 640 boards
- **seeds/candidate_profile.md** — the profile jobs are scored against (written from devmaster-cv, claim levels kept, no location)
- **seeds/match_prompt.md** — the matcher's rubric, rules and output shape; its hash is each row's `prompt_version`
- **seeds/cv_sources.md** — the scrubbed devmaster-cv pack that tailored CVs are written from (built by `cv sources`)
- **seeds/cv_writer_prompt.md**, **seeds/cv_review_prompt.md** — the CV writer's and recruiter reviewer's instructions
- **tests/** — pytest. tests/fixtures holds recorded real responses (made by scripts/record_fixtures.py).

## Running
python -m jd_aggregator seed | poll [--source NAME] [--force] | relang | reclassify | match todo FILE | match results FILE | match import FILE [--run NAME] | match rescore | cv todo FILE | cv save FILE | cv sources [--src DIR] | cv pdfs | prefs set FILE | serve [--port N]

`seed` also loads seeds/company_sectors.csv. `reclassify` recomputes every job's fields and every company's sector.

- **First time:** `seed`, then `poll --force`, then `serve`. A full poll takes about 8 minutes. Aggregators are fetched in background threads while the ATS pass runs with 8 workers; the 1 req/s per-host limit still holds, so getro (22 networks on one API host, ~7.5 min) sets the floor. The ATS pass took 4 min for ~9.8k jobs on 2026-10-21. Each ATS board is committed as it lands, so the UI fills in during the run. All SQLite writes stay on the main thread.
- **Scheduling:** launchd/com.davidc.jd-aggregator.poll.plist runs `poll` every 15 minutes, and each source decides whether it is due. launchd/com.davidc.jd-aggregator.web.plist keeps the UI running.

  Install:
  `cp launchd/*.plist ~/Library/LaunchAgents/ && launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.davidc.jd-aggregator.poll.plist` (same for `.web`).

  Stop:
  `launchctl bootout gui/$(id -u)/com.davidc.jd-aggregator.poll`.
- **Rebuild from scratch:** `rm data/jd_aggregator.db && python -m jd_aggregator seed && python -m jd_aggregator poll --force`.
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
