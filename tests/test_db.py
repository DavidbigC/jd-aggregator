def test_schema_creates_all_tables(conn):
    names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type IN ('table', 'view')")}
    assert {"companies", "boards", "jobs", "sightings", "source_runs", "jobs_fts"} <= names


def test_fts_trigram_matches_substrings(conn):
    conn.execute("INSERT INTO jobs_fts (rowid, title, company, description) VALUES (1, 'Rust工程师', '未具名', 'crypto quant')")
    assert conn.execute("SELECT rowid FROM jobs_fts WHERE jobs_fts MATCH '\"工程师\"'").fetchone()[0] == 1
    assert conn.execute("SELECT rowid FROM jobs_fts WHERE jobs_fts MATCH '\"quan\"'").fetchone()[0] == 1
