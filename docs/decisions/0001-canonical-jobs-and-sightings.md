# 0001 — Canonical jobs + sightings

**Problem.** The same job appears on up to 8 sources. Research on 16,226 real records found:
- **Same job id:** 42% were duplicates.
- **Same job under different job ids:** about 1,000 more groups, mostly per-city copies and companies running two ATSs.

The UI must show each job once, but still list every source.

**Options considered.**
1. **Store raw postings and group them at query time.** Simple writes, but slow and complex reads. The grouping logic would run on every page view.
2. **Canonical `jobs` table plus a `sightings` table, resolved at ingest.** Each posting either attaches to an existing job or creates one.
3. **LLM-based dedup.** Accurate but costly and slow. That belongs to the later scoring phase.

**Decision.** Option 2.

The matching ladder is: ATS id → company + normalised title → description similarity ≥ 0.85, with a "probable" fallback when a description is missing. Sightings record kind and match quality, so the UI can show "seen on 5 sources".

**Consequences.**
- Reads are simple and fast.
- Merge mistakes are sticky: a wrong attach stays until the database is rebuilt. Sightings marked `probable` make the risky ones visible.
- Rebuilding is cheap: delete data/jd_aggregator.db and poll again.
