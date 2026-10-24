# 0008: Claude does the LLM work; the app calls no LLM

Date: 2026-10-24. Status: accepted. Supersedes the provider part of 0005; 0006's truth rules and prompts stay.

## Problem
DeepSeek scored jobs and wrote CVs inside the app (0005, 0006). It proved too fragile for the work:
- empty or non-JSON replies;
- CVs that broke the code rules and needed retries;
- an invented claim that reached a finished CV: "面向 Ave.ai 的 7m 用户", which read as though David already served Ave.ai's users.

David wants Claude to do all the LLM work from now on, and wants the DeepSeek key entry kept in Settings.

## Options considered
1. **Keep DeepSeek and tune its prompts further.** That keeps the failures above.
2. **Call the Anthropic API from the app.** The app would run the same passes with a Claude key. It needs a key and spends money per run, and David asked for Claude, working with them in Claude Code, to do the work.
3. **Claude in Claude Code, with the app as queue and checker.** The app writes what needs doing to a file. Claude does the judgement and the code loads the results through the same validation and rules as before.

## Decision
Option 3.
- **Scoring:** `match todo` → Claude answers in the `seeds/match_prompt.md` shape → `match results`. `clean()` and `verdict()` still decide the verdict, so Claude scores and the rules decide, as before.
- **CVs:** `cv todo` → Claude writes, reviews (`seeds/cv_review_prompt.md`) and revises from `seeds/cv_sources.md` → `cv save`, which refuses any CV that fails `problems()` and saves the PDF.
- **Preferences:** `prefs set`, through the same `validate()`. The chat is removed.
- **Stamps:** the model stamp is `claude-opus-5-5`, so every DeepSeek result reads as due for redoing.
- **Removed:** the DeepSeek passes, the background threads, the cost estimates, and the Run, Tailor and Rewrite buttons.
- **Kept:** `deepseek.balance()`, the keystore and the Settings key card.

## Consequences
- **Nothing runs without a Claude Code session.** New jobs from the poll wait on `/shortlist` ("N waiting to be scored") until David asks Claude.
- **No per-run API cost** in the app. `cost_usd` is 0 on new rows.
- **The Ultra CV Master still never goes into a CV.** Claude works only from the scrubbed pack, the same as the earlier pipeline.
- **Going back to an in-app LLM** would mean restoring a client and the pass functions from git history. The checks, stamps and storage are unchanged.
