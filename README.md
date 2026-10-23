# JD Aggregator

A local job-search app for one person, built for crypto and Web3 roles. It runs on a Mac and serves its UI at http://127.0.0.1:8765. There is no cloud service.

It does five things:

- **Collects job ads** from about 640 sources and merges duplicates into one job. The sources are company hiring systems (Greenhouse, Lever, Ashby and 11 more), crypto job boards, Telegram channels, and general sites such as LinkedIn and SEEK, in many languages.
- **Fills in** each job's full description, and tags its role, seniority, countries and remote scope.
- **Scores the fit** of each job against the candidate profile with an LLM, and builds a shortlist sorted mostly by how much the candidate wants the job.
- **Tailors a CV** for each shortlisted job. A writer drafts it, a recruiter-style reviewer critiques it, the writer revises, and a final screen checks it. Code-level checks guard the truth rules.
- **Saves every finished CV as a PDF** in one folder, ready to upload to job sites (see below).

DeepSeek is the LLM today. It is due to be replaced.

## Setup

```sh
python3.14 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/python -m playwright install chromium-headless-shell  # renders CV PDFs
.venv/bin/python -m jd_aggregator seed          # load the board registry
.venv/bin/python -m jd_aggregator poll --force  # first full poll, about 8 minutes
.venv/bin/python -m jd_aggregator serve         # http://127.0.0.1:8765
```

Then open **Settings** and do two things:

- Add a DeepSeek API key. It is checked, then stored in the macOS Keychain.
- Add the contact line printed under the name on every CV. It is stored only in the local database.

## Commands

```
python -m jd_aggregator seed | poll [--source NAME] [--force] | relang | reclassify
                        | match import FILE | match rescore
                        | cv sources [--src DIR] | cv pdfs
                        | serve [--port N]
```

To poll every 15 minutes and keep the UI running, install the launchd agents in `launchd/`. ARCHITECTURE.md has the install steps.

## CV PDFs

Every finished CV is saved as a PDF in **`~/Documents/JD Aggregator CVs/`**. Set the `JD_AGGREGATOR_CVS` environment variable to use another folder, for example a Google Drive or iCloud folder. Files are named `<Name> - <Company> <Job title>.pdf`, and rewriting a CV replaces its file.

In the app:

- **Download PDF** on a CV re-renders the PDF with the current contact line and downloads it.
- **Show in Finder** opens the folder with the file selected.

`python -m jd_aggregator cv pdfs` writes the PDFs for every finished CV.

## Data and privacy

- `data/` holds the SQLite database, the logs and the contact line. It is git-ignored.
- The API key is kept only in the macOS Keychain, or in the `DEEPSEEK_API_KEY` environment variable.
- `seeds/` holds the candidate's own material: the profile, the CV source pack and the prompts. Replace these to use the app for someone else.
- The contact line is never sent to the LLM. Generated CVs are checked for phone numbers, emails and dollar figures before they are saved.

## Docs

- ARCHITECTURE.md: how the app works.
- docs/decisions/: the decision records.
- CHANGELOG.md: changes by date.
