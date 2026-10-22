# 0005: DeepSeek as Job Radar's LLM, key in the Keychain, preferences in SQLite

Date: 2026-10-22. Status: accepted (Phases A–B built first; the matcher was added in Phase C, see the last section).

## Problem
Job Radar needs an LLM for two jobs:
- turning David's own words into structured job preferences;
- later, scoring jobs against those preferences and the CV.

David wants all LLM work done inside the app, by a provider whose key they load from the web UI. Claude reviews the results rather than producing them.

## Options considered
1. **Anthropic API (Haiku triage + Opus evaluation).** This was the earlier matcher plan. It has strong judgement, but costs about 10× more, and David chose otherwise.
2. **DeepSeek API.** It is OpenAI-compatible over plain HTTPS, and very cheap: deepseek-flash costs $0.30 per 1M input tokens and $1.20 per 1M output tokens at peak, and off-peak hours are half price. It has a 1M context and a JSON output mode.
3. **A local model.** It would keep everything private, but judgement is weaker and it needs model weights and GPU time on the laptop.

**Where to keep the key:**
- in SQLite;
- in a dotfile under `data/`;
- in the macOS Keychain.

**Where to keep preferences:**
- in a YAML file in `seeds/`;
- in SQLite.

## Decision
- **Provider: DeepSeek, called with `httpx`** (`deepseek.py`), so there is no SDK dependency. The chat uses `deepseek-flash` with thinking off and `response_format: json_object`. An empty reply, which DeepSeek's docs say can happen, is retried once.
- **Key: the macOS Keychain** (service `jobradar.deepseek`), through the built-in `security` tool.
  - The key is written through `security -i` on stdin, so it never appears in the process list.
  - It is checked against `^sk-[A-Za-z0-9]{16,}$` before storing, and confirmed with the free `GET /user/balance` call.
  - `DEEPSEEK_API_KEY` in the environment overrides the Keychain.
  - The database, which Claude reads during reviews, never holds the key.
- **Preferences: SQLite.**
  - The `preferences` table keeps every version; the newest row is current.
  - The `pref_messages` table holds the chat, and each proposed change is stored with the assistant message as `pending`, `applied` or `discarded`.
  - DeepSeek can only propose; David's **Apply** writes the new version. The server checks every proposal against `prefs.SCHEMA` and drops unknown keys and disallowed values.
  - The assistant's instructions are in `seeds/prefs_assistant_prompt.md`, versioned in git.

## Consequences
- **Data leaves the machine.** The chat history, the current preferences and, later, the condensed candidate profile and job ads go to DeepSeek, a China-based provider.
  - The prompt forbids contact details, account IDs, wallets and trading profits.
  - The profile already follows that rule.
- **Keychain prompts.** The Keychain is macOS-only. If the server runs under launchd, the first read may trigger a Keychain permission prompt.
- **Running elsewhere.** On another machine, the key comes from the environment variable instead.
- **Rolling back.** Preferences are versioned, so a bad change can be undone by applying an older version (a UI for that is not built yet).
- **Re-scoring.** The matcher can stamp each result with the preferences version and re-score jobs when it changes.
- **Claude's role.** Claude does not score jobs. It reviews DeepSeek's chat proposals and, later, its scores, and its feedback lands in the web app.

## Addendum: the matcher (Phase C)

**Problem.** Score the prefiltered jobs (about 130 in a 14-day window) against David's profile and preferences, inside the app, with David starting each run.

**Options considered.**
1. A cheap triage model, then a deep model (the earlier Claude plan: Haiku then Opus).
2. One stage on `deepseek-v4-pro` with thinking.
3. One stage on `deepseek-flash`.

**Decision.**
- **One stage on `deepseek-v4-pro`, thinking on, JSON mode.** At about $0.01–0.02 per job, a triage stage saves little and risks dropping good jobs. Flash was too unreliable in JSON mode during the preferences chat.
- **The verdict is computed in code** from DeepSeek's three scores and quoted knockouts, so a model change cannot quietly move the thresholds.
- **The profile and prompt are files in `seeds/`**, sent first and byte-stable so the prefix cache covers them. Every row is stamped with the model, the prompt and profile hashes and the preferences version; a change to any of them, or to the ad, makes the job due for re-scoring.
- **Runs start from the Shortlist page** and show the cost before anything is spent. Runs are a background thread in the server process, like manual source polls.

**Consequences.**
- **More data leaves the machine:** the candidate profile and each prefiltered job ad go to DeepSeek. The profile has no contact details, location, account IDs or trading profits.
- **Speed and cost:** about 50 seconds and roughly 3,600 output tokens per job (mostly reasoning). A full run of about 130 jobs takes about 15 minutes at 8 jobs at a time, and costs about $1.30 off-peak or $2.70 at peak.
- **Preference changes re-score everything.** Any change to the preferences makes every job due again; the confirm step shows the count and cost first.
- **Restarts:** a server restart during a run leaves it marked interrupted. Pressing Run matcher again picks up the jobs that were not scored.

**Prompt v2 (2026-10-22).** The first run's review (job_related `docs/research/2026-10-22-deepseek-matcher-review.md`) showed DeepSeek hiding good analyst jobs behind years and skill "knockouts". Knockouts are now eligibility only (right to work, location, language, licence), enforced in `clean()`; years and skills lower the recruiter score. Unset right to work counts as not confirmed, so country-limited jobs are knockouts until David states their rights.
