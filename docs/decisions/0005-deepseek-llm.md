# 0005: DeepSeek as Job Radar's LLM, key in the Keychain, preferences in SQLite

Date: 2026-10-22. Status: accepted (Phases A–B built; the matcher in Phase C will use the same client).

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
