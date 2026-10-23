# 0006: Tailored CV per job, written and reviewed by DeepSeek

Date: 2026-10-22. Status: accepted.

## Problem
David wants a CV tailored to each job, ready when the job is opened, so applying takes minutes. The facts must come from the audited master CV (`devmaster-cv`): 2026 work is AI-built under David's direction and must never be claimed as their own code. Private details must never reach DeepSeek: phone, email, address, and dollar P&L or capital figures.

## Options considered
1. **One DeepSeek call that writes the CV.** Cheapest, but nothing checks it. Run 1 of the matcher showed DeepSeek drifts on rules when nothing pushes back.
2. **Writer, then a tough recruiter review, then a revision (three calls).** About 3× the cost of option 1, which is still about 5 cents a CV. The review catches invented claims, missing keywords and weak bullets, and David sees what changed.
3. **Claude writes the CVs.** This is against the decision in 0005: in-app LLM work is DeepSeek's.

**Where the facts come from:**
- `David Chen - Ultra CV Master.md`: it has the contact details and P&L figures, so it is ruled out.
- The old tailored CVs: they predate the ownership audit, so they are ruled out.
- `devmaster-cv`, scrubbed by code: **chosen.**

**Output format:**
- Markdown from DeepSeek. The app has no Markdown library, and the layout would drift between CVs.
- **Structured JSON that the app renders itself: chosen.** The same layout every time, `resume.css` styling, and the contact header added by the app.

**PDF:**
- `md-to-pdf` or WeasyPrint: they need Node or extra native libraries.
- **The browser's Save as PDF on a print page styled with `resume.css`: chosen.** It gives the same output as `md-to-pdf`, which also renders through Chrome, with nothing to install.

## Decision
- **Pipeline.** Option 2: three calls to `deepseek-v4-pro` with thinking on and JSON mode.
  - The system message is the source pack plus `seeds/cv_writer_prompt.md`, or `seeds/cv_review_prompt.md` for the review.
  - The pack comes first and is byte-stable, so the prefix cache covers it in all three calls.
- **Source pack.** `python -m jd_aggregator cv sources` builds `seeds/cv_sources.md` from devmaster-cv:
  - drops dollar amounts other than the "$1M volume" ranking threshold;
  - drops any email or phone line;
  - drops the README's PDF and repo-upkeep sections.

  Its hash is stamped on every CV.
- **Checks in code after the writer and reviser passes.** A reply fails if it has:
  - an email;
  - a phone number;
  - a dollar amount;
  - he/she or 他/她;
  - no FLOKI or Dragon Race entry.

  A failed reply is retried once, with the problems named.
- **Contact header.** The app adds it when rendering: David's name, the public links from the pack, and a contact line from Settings that is stored only in the local database. DeepSeek never sees the contact line.
- **Storage.** A `tailored_cvs` table holds the draft, the review and the final version. The latest row per job is shown, and older rows are kept. A small `settings` table holds the contact line.
- **When CVs are made.** Only when David presses a button: one on each job, or "Tailor CVs for N shortlisted jobs", which shows the cost first. They are never made automatically after a matcher run.
- **Language.** The CV follows the ad: a Chinese ad gets a Chinese CV.

## Consequences
- **Cost and time.** A CV costs about $0.04–0.07 and takes 2–4 minutes. The review scores the first draft; a fourth call to re-score the final version was left out to save time and money.
- **Data sent to DeepSeek.** devmaster-cv content goes to DeepSeek; it has public links and no private data. The contact line stays local.
- **When a CV goes out of date.** If devmaster-cv or a prompt changes, existing CVs show "made from older sources" until David presses Rewrite.
- **Truth checks.** The code can check form (leaks, required roles), not truth. The recruiter pass and David's read before sending are the checks on truth.

## Update 2026-10-23: CVs that sell, and a score for the final CV
The first five real CVs (research: `~/job_related/docs/research/2026-10-23-cv-quality.md`) showed four problems:
- the shown score was the draft's, and the revision introduced new errors (a merged claim, a title David never held, reviewer wording pasted in);
- the reviewer overrode the writer's rules;
- the CVs volunteered weaknesses;
- every CV printed to about 1⅓ pages.

Changes:
- **Goal.** The writer's goal is now to make the screening recruiter want to call David, within the unchanged truth rules. It never sells against David: no volunteered shortfalls, no hedges.
- **Summary.** It ends with a "why this role" sentence grounded in a real pack fact.
- **Length.** Two full pages, about 700–900 words.
- **Reviewer.**
  - It plays the in-house recruiter. Its score measures how compelling the CV is, and any invented claim caps it at 40.
  - Fixes are instructions, never finished copy.
  - It never asks for a title David hasn't held, or for a keyword no pack line states.
- **A fourth call screens the final CV.** Its score is what's stored and shown, and its issues appear as "Still weak". When the screen finds an invented claim or a must_fix, there is one repair revision and a second screen. The first test round showed why: the push to sell produced "drove the roadmap" and the ad's "decision memos" in the revision, and the screen caught them but nothing fixed them. This brings a CV to about $0.12–0.15 and 5–8 minutes; David said cost is not a concern.
- **More code checks:**
  - hedges;
  - "trader" in the headline or a title;
  - FLOKI shown as current (David left in April 2026);
  - sentence-like skills;
  - a figure repeated across experience, projects and highlights;
  - a word cap;
  - the independent entry missing.
- **Experience order.** "Independent On-Chain Market Maker & Arbitrageur | 2021 – Present (full-time since May 2026)" comes first, as David's current work. The timeline sits in the dates, not in a bullet.
- **Summary repeats.** The summary may restate the two headline numbers that the experience proves. Nothing else appears twice.
