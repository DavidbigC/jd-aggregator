import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS companies (
  id INTEGER PRIMARY KEY,
  key TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  website TEXT,
  created_at TEXT NOT NULL,
  sector TEXT,
  sector_source TEXT
);
CREATE TABLE IF NOT EXISTS boards (
  id INTEGER PRIMARY KEY,
  company_id INTEGER NOT NULL REFERENCES companies(id),
  ats TEXT NOT NULL,
  slug TEXT NOT NULL,
  origin TEXT NOT NULL,
  enabled INTEGER NOT NULL DEFAULT 1,
  last_polled_at TEXT,
  last_status TEXT,
  last_count INTEGER,
  crypto_only INTEGER NOT NULL DEFAULT 0,
  UNIQUE (ats, slug)
);
CREATE TABLE IF NOT EXISTS jobs (
  id INTEGER PRIMARY KEY,
  company_id INTEGER NOT NULL REFERENCES companies(id),
  title TEXT NOT NULL,
  title_key TEXT NOT NULL,
  description TEXT,
  desc_from_ats INTEGER NOT NULL DEFAULT 0,
  locations TEXT NOT NULL DEFAULT '[]',
  regions TEXT NOT NULL DEFAULT '[]',
  remote INTEGER NOT NULL DEFAULT 0,
  salary TEXT,
  apply_url TEXT,
  posted_at TEXT,
  first_seen_at TEXT NOT NULL,
  last_seen_at TEXT NOT NULL,
  lang TEXT,
  enriched_at TEXT,
  enrich_status TEXT,
  role TEXT,
  seniority TEXT,
  countries TEXT NOT NULL DEFAULT '[]',
  remote_scope TEXT
);
CREATE INDEX IF NOT EXISTS jobs_company_title ON jobs (company_id, title_key);
CREATE INDEX IF NOT EXISTS jobs_last_seen ON jobs (last_seen_at);
CREATE INDEX IF NOT EXISTS jobs_lang ON jobs (lang);
CREATE INDEX IF NOT EXISTS jobs_role ON jobs (role);
CREATE INDEX IF NOT EXISTS jobs_seniority ON jobs (seniority);
CREATE INDEX IF NOT EXISTS companies_sector ON companies (sector);
CREATE TABLE IF NOT EXISTS sightings (
  id INTEGER PRIMARY KEY,
  job_id INTEGER NOT NULL REFERENCES jobs(id),
  source TEXT NOT NULL,
  kind TEXT NOT NULL,
  source_job_id TEXT NOT NULL,
  ats_key TEXT,
  url TEXT,
  url_key TEXT,
  detail_url TEXT,
  location TEXT,
  match TEXT NOT NULL DEFAULT 'exact',
  first_seen_at TEXT NOT NULL,
  last_seen_at TEXT NOT NULL,
  UNIQUE (source, source_job_id)
);
CREATE INDEX IF NOT EXISTS sightings_ats ON sightings (ats_key);
CREATE INDEX IF NOT EXISTS sightings_job ON sightings (job_id);
CREATE INDEX IF NOT EXISTS sightings_kind ON sightings (kind, job_id);
CREATE TABLE IF NOT EXISTS source_runs (
  id INTEGER PRIMARY KEY,
  source TEXT NOT NULL,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  status TEXT NOT NULL,
  fetched INTEGER NOT NULL DEFAULT 0,
  new_jobs INTEGER NOT NULL DEFAULT 0,
  error TEXT
);
CREATE INDEX IF NOT EXISTS source_runs_source ON source_runs (source, id);
CREATE TABLE IF NOT EXISTS skipped (
  source TEXT NOT NULL,
  source_job_id TEXT NOT NULL,
  at TEXT NOT NULL,
  PRIMARY KEY (source, source_job_id)
);
CREATE TABLE IF NOT EXISTS match_evaluations (
  job_id INTEGER PRIMARY KEY REFERENCES jobs(id),
  run TEXT NOT NULL,
  verdict TEXT NOT NULL,
  track TEXT,
  rec INTEGER,
  hm INTEGER,
  want INTEGER,
  priority INTEGER,
  why TEXT,
  risk TEXT,
  start_cv TEXT,
  label TEXT,
  label_note TEXT,
  labelled_at TEXT,
  created_at TEXT NOT NULL,
  reason TEXT,
  model TEXT,
  prompt_version TEXT,
  profile_hash TEXT,
  prefs_version INTEGER,
  description_hash TEXT,
  result TEXT
);
CREATE TABLE IF NOT EXISTS match_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  status TEXT NOT NULL,
  model TEXT NOT NULL,
  prefs_version INTEGER,
  planned INTEGER NOT NULL DEFAULT 0,
  evaluated INTEGER NOT NULL DEFAULT 0,
  failed INTEGER NOT NULL DEFAULT 0,
  input_hit INTEGER NOT NULL DEFAULT 0,
  input_miss INTEGER NOT NULL DEFAULT 0,
  output_tokens INTEGER NOT NULL DEFAULT 0,
  cost_usd REAL NOT NULL DEFAULT 0,
  error TEXT
);
CREATE TABLE IF NOT EXISTS preferences (
  version INTEGER PRIMARY KEY AUTOINCREMENT,
  data TEXT NOT NULL,
  source TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS pref_messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  role TEXT NOT NULL,
  content TEXT NOT NULL,
  proposal TEXT,
  status TEXT,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS tailored_cvs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  job_id INTEGER NOT NULL REFERENCES jobs(id),
  created_at TEXT NOT NULL,
  finished_at TEXT,
  status TEXT NOT NULL,
  stage TEXT,
  model TEXT NOT NULL,
  prompt_version TEXT,
  sources_hash TEXT,
  draft TEXT,
  review TEXT,
  final TEXT,
  final_review TEXT,
  score INTEGER,
  cost_usd REAL NOT NULL DEFAULT 0,
  error TEXT
);
CREATE INDEX IF NOT EXISTS tailored_cvs_job ON tailored_cvs (job_id, id);
CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
CREATE VIRTUAL TABLE IF NOT EXISTS jobs_fts USING fts5 (title, company, description, tokenize = 'trigram');
"""

ADDED_COLUMNS = [
    ("boards", "crypto_only", "INTEGER NOT NULL DEFAULT 0"),
    ("jobs", "lang", "TEXT"),
    ("jobs", "enriched_at", "TEXT"),
    ("jobs", "enrich_status", "TEXT"),
    ("sightings", "detail_url", "TEXT"),
    ("companies", "sector", "TEXT"),
    ("companies", "sector_source", "TEXT"),
    ("jobs", "role", "TEXT"),
    ("jobs", "seniority", "TEXT"),
    ("jobs", "countries", "TEXT NOT NULL DEFAULT '[]'"),
    ("jobs", "remote_scope", "TEXT"),
    ("match_evaluations", "reason", "TEXT"),
    ("match_evaluations", "model", "TEXT"),
    ("match_evaluations", "prompt_version", "TEXT"),
    ("match_evaluations", "profile_hash", "TEXT"),
    ("match_evaluations", "prefs_version", "INTEGER"),
    ("match_evaluations", "description_hash", "TEXT"),
    ("match_evaluations", "result", "TEXT"),
    ("tailored_cvs", "final_review", "TEXT"),
]


def connect(path) -> sqlite3.Connection:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    for table, col, ddl in ADDED_COLUMNS:
        cols = {r["name"] for r in conn.execute(f"PRAGMA table_info({table})")}
        if cols and col not in cols:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {ddl}")
    conn.executescript(SCHEMA)
    return conn
