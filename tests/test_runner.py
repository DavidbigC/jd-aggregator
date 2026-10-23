from jd_aggregator import runner
from jd_aggregator.models import Posting

KRAKEN_URL = "https://jobs.ashbyhq.com/kraken.com/993557d9-7482-4f63-aae0-5817998b2368"


def test_due_sources_respects_intervals(conn):
    conn.execute("INSERT INTO source_runs (source, started_at, status) VALUES ('jobstash', '2026-10-21T11:00:00Z', 'ok')")
    assert runner.due_sources(conn, "2026-10-21T12:00:00Z", only=["jobstash", "cryptojobslist"]) == ["cryptojobslist"]
    assert runner.due_sources(conn, "2026-10-21T12:00:00Z", force=True, only=["jobstash"]) == ["jobstash"]


def test_run_source_ingests_and_discovers_boards(conn, monkeypatch):
    fake = lambda http: [Posting(source="fake", source_job_id="1", company="Payward, Inc.", title="Eng", url=KRAKEN_URL)]
    monkeypatch.setitem(runner.AGGREGATORS, "fake", fake)
    r = runner.run_source(conn, None, "fake")
    assert (r["status"], r["fetched"], r["new_jobs"]) == ("ok", 1, 1)
    assert tuple(conn.execute("SELECT ats, slug, origin FROM boards").fetchone()) == ("ashby", "kraken.com", "discovered")


def test_run_source_records_errors(conn, monkeypatch):
    monkeypatch.setitem(runner.AGGREGATORS, "boom", lambda http: 1 / 0)
    r = runner.run_source(conn, None, "boom")
    assert r["status"] == "error" and "ZeroDivisionError" in r["error"]
    assert conn.execute("SELECT status FROM source_runs WHERE source = 'boom'").fetchone()[0] == "error"


def test_ats_run_records_per_board_status(conn, monkeypatch):
    conn.execute("INSERT INTO companies (key, name, created_at) VALUES ('acme', 'Acme', '2026-10-21T00:00:00Z')")
    conn.execute("INSERT INTO boards (company_id, ats, slug, origin) VALUES (1, 'ashby', 'ok', 'seed'), (1, 'lever', 'bad', 'seed')")
    monkeypatch.setitem(runner.ADAPTERS, "ashby", lambda http, slug, co: [
        Posting(source=f"ats:ashby:{slug}", source_job_id="1", company=co, title="Eng", from_ats=True)])
    monkeypatch.setitem(runner.ADAPTERS, "lever", lambda http, slug, co: 1 / 0)
    r = runner.run_source(conn, None, "ats")
    assert r["status"] == "ok" and r["new_jobs"] == 1
    st = dict(conn.execute("SELECT slug, last_status FROM boards").fetchall())
    assert st["ok"] == "ok" and st["bad"].startswith("error")


def test_poll_prefetches_aggregators_and_ingests_each(conn, monkeypatch, tmp_path):
    monkeypatch.setattr(runner, "DATA_DIR", tmp_path)
    monkeypatch.setattr(runner, "AGGREGATORS", {
        "a": lambda http: [Posting(source="a", source_job_id="1", company="Acme", title="Eng")],
        "b": lambda http: 1 / 0})
    results = dict(runner.poll(conn, sources=["a", "b"], force=True, http=object(), log=lambda m: None))
    assert results["a"]["new_jobs"] == 1 and results["b"]["status"] == "error"


def test_crypto_only_boards_keep_only_web3_postings(conn, monkeypatch):
    conn.execute("INSERT INTO companies (key, name, created_at) VALUES ('dbs', 'DBS', '2026-10-21T00:00:00Z')")
    conn.execute("INSERT INTO boards (company_id, ats, slug, origin, crypto_only) VALUES (1, 'workday', 'dbs', 'seed', 1)")
    monkeypatch.setitem(runner.ADAPTERS, "workday", lambda http, slug, co: [
        Posting(source="ats:workday:dbs", source_job_id=str(i), company=co, title=t, from_ats=True)
        for i, t in enumerate(["Digital Assets Custody Lead", "Branch Manager"])])
    r = runner.run_source(conn, None, "ats")
    assert r["fetched"] == 1
    assert [t for (t,) in conn.execute("SELECT title FROM jobs")] == ["Digital Assets Custody Lead"]
