# 0004 — Match evaluations and the Shortlist page

**Date:** 2026-10-22

## Problem

Jobs are now scored for fit against David's CV:
- by hand for now;
- by an LLM pipeline later (see `job_related/docs/prompts/2026-10-22-job-matcher-agent-prompt.md`).

The scores and David's own Yes/Maybe/No labels need a home that David actually uses. That means the web app, not markdown reports. A re-run of the scoring must never lose a label, because the labels are how the matcher gets calibrated.

## Options considered

1. **Keep results in JSON or markdown files.** Rejected: David only uses the web app.
2. **Add score columns to `jobs`.** Rejected: it mixes collected facts with opinions about them, and scoring runs would churn a hot table.
3. **A separate `match_evaluations` table, one row per job, with the label in the same row.** Chosen.

## Decision

- **`match_evaluations`** is keyed by `job_id`.
  - It holds the latest verdict, track, three scores (`rec`, `hm`, `want`), `priority`, `why`, `risk`, `start_cv` and the `run` that produced it.
  - It also holds David's `label` (Y/M/N), `label_note` and `labelled_at`.
- **Importing a new run** upserts the score fields and never writes the label fields.
- **Scores are plain integer columns,** not JSON, so the page can sort and filter in SQL.
- **`python -m jobradar match import <file.json>`** loads results. The LLM pipeline will write through the same function.
- **`/shortlist`** shows evaluated jobs grouped by verdict, with Y/M/N buttons and a note. It reuses the existing job detail pane, so the full ad is one click away.

## Consequences

- There's only the latest evaluation per job, with no history. If verdict drift needs measuring later, add a `match_runs` log; don't widen this table.
- A label belongs to the job, not to a run, so it stays meaningful when a later run re-scores the job.
