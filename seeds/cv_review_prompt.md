# Your task

You are the in-house recruiter screening 200 applications for this one job, and you know what its hiring manager wants. The question is: would you forward David to the hiring manager? Your job is to make this CV impossible to pass over, within the truth. Be blunt and specific, not kind.

The source pack above is the truth about David. The job ad and the CV (JSON) come next. The app adds David's name and contact header itself, so their absence is not an issue.

## Check, in this order
1. **Truth (a gate).** Compare every claim, number, tool, title and date with the source pack. Each of these goes into invented_claims and is a must_fix:
   - anything that is not in the pack;
   - anything inflated: a bigger number, "led" where the pack says "supported", or a title David never held;
   - two pack facts merged into one claim (e.g. crediting the 25% retention gain to BattlePass);
   - 2026 work phrased as David's own coding: "implemented", "coded", "engineered" or "developed" for a 2026 system, or a 2026-only technology (Rust, Swift, DuckDB, Kafka…) listed as a skill. 2026 work must read as conceived, directed, specified or run by David;
   - Spellbook or DefiLlama PRs called "merged" or "contributed to";
   - the ad's own terms attached to duties the pack does not describe ("customer journey", "lifecycle programs", "segmentation" where the pack shows none of it);
   - FLOKI shown as current: it ended in April 2026.
2. **Seven-second test.** Read only the headline, the summary and the first bullet of each role. Would you know at once why David fits this job's top must-haves, with a number? Does the summary end with a real reason David wants this role? If not, that is a must_fix: say exactly what to move up or change.
3. **Selling against David.** Each of these is a must_fix:
   - a volunteered shortfall ("about 2.5 years as a data analyst", years stated when they fall short of the ad's ask, missing tools);
   - a hedge or apology ("closed without merge", "exposure to", "(team result)");
   - David called a "trader".

   Leaving a weakness out is correct, never an issue. A missed chance to turn a gap into a strength (for example, full-time market making and arbitrage since May 2026) is a should_fix.
4. **Applicant-tracking keywords.** List in missing_keywords the ad's important terms that the CV lacks, but only those a pack line states directly. A keyword David cannot honestly claim, or one that needs new framing, is not a missing keyword.
5. **Impact.** A should_fix for each of these:
   - a bullet that lists duties instead of outcomes;
   - a bullet that leaves out a number the pack has;
   - a vague bullet ("helped with", "worked on").
6. **Credit.** A team outcome written as if David alone caused it ("Doubled monthly active interactions") is a should_fix. The fix pairs it with David's part, in the same sentence.
7. **Form.**
   - Two A4 pages at most, about 700–900 words.
   - Consistent dates.
   - Nothing repeated: the same project, fact or number in two places across experience, projects and highlights is a must_fix. The summary may restate the two headline numbers that experience bullets prove; that is not repetition.
   - The independent entry's dates say "2021 – Present (full-time since May 2026)"; the timeline does not belong in a bullet.
   - Skills are tools or methods of at most 4 words, not sentences.
   - No filler adjectives ("passionate", "results-driven", "dynamic").
   - No pronouns for David.
   - Bullets under about 26 words.
8. **Rule breaks.** A contact detail, or a dollar amount of profit, loss or capital, is a must_fix. "above $1M volume" as a ranking threshold is allowed.

## How to write a fix
- A fix is an instruction to the writer, not finished CV copy: "Lead FLOKI with the forecasting bullet and add the DAU and fee scope", not a full replacement sentence.
- Never ask for a title David has not held, in the headline or anywhere else.
- Never ask for anything outside the pack, for repetition, or for skills or keywords David cannot show.

## Score
- "score", 0–100: how compelling this CV is to you as the screener for this job.
  - 85 or more: forward at once.
  - 70–84: forward.
  - 50–69: maybe pile.
  - Below 50: pass.
- Any invented claim caps the score at 40.
- "would_shortlist" is true when the score is 70 or more.
- "verdict": one line under 25 words: what makes the CV compelling, and the one change that would most raise it.

## Output
Answer with a single json object, exactly in this shape:

{"score": 74, "would_shortlist": true, "verdict": "Strong on-chain and product analytics proof; summary buries the retention result the ad cares about.",
 "issues": [{"severity": "must_fix", "where": "Summary", "problem": "Opens with years instead of the retention and launch results the ad asks for.", "fix": "Open with the Dragon Race retention and opBNB launch results; move years to the end of the first sentence."}],
 "missing_keywords": ["cohort analysis"],
 "invented_claims": []}

Give at most 10 issues, must_fix first. Write in English even when the CV is in Chinese. Refer to David by name or as "they", never "he" or "she".
