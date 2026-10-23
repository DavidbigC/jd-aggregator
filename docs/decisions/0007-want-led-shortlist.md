# 0007: Shortlist led by Want, not by the recruiter score

Date: 2026-10-23. Status: accepted.

## Problem
Priority was rec·hm·want/10000. The verdict rules gated on `rec` (would a recruiter shortlist David's master CV as it is). Jobs David wanted and could do were hidden or sorted low because the untailored CV would not pass a screen. Every shortlisted job now gets a tailored CV, and getting past the screen is that CV's job, so Rec is the score David can most change. David asked for Want to count much more than the recruiter recommendation.

## Options considered
1. Keep the product, but sort by Want first. Rec would still gate verdicts and hide jobs.
2. **A weighted geometric mean, want^0.5 · hm^0.35 · rec^0.15, plus verdict rules gated on Want and HM. Chosen.** HM still matters, because the interviews after the screen test real ability.
3. Drop Rec entirely. That loses a useful signal of how much CV work a job needs.

## Decision
- **Priority** is `match.priority()`, a 0–100 weighted geometric mean.
- **Verdicts:**
  - knockouts and Want < 45 are still skipped;
  - apply now needs want ≥ 65, hm ≥ 60 and rec ≥ 50;
  - tailor then apply needs want ≥ 55 and hm ≥ 45, or the old rec ≥ 45 and hm ≥ 50, so no previously shown job disappears;
  - stretch needs want ≥ 55 and hm ≥ 35;
  - quant and backend jobs are capped at stretch when hm ≥ 40.
- **`python -m jobradar match rescore`** re-derives verdicts and priorities from the stored result JSON, without calling DeepSeek. Labels are kept.
- **Display.** Shortlist rows show Want first and in bold, then HM, then Rec muted.

## Consequences
- The first rescore moved the shortlist from 9 to 13 jobs: 3 skip → stretch, 1 skip → tailor, 1 tailor → apply now.
- More stretches are shown. Rec stays visible as a guide to how much a CV must do.
- The matcher prompt is unchanged: DeepSeek still scores all three honestly, and only the code's use of them changed.
