import json

import pytest
from fastapi.testclient import TestClient

from jobradar import deepseek, enrich, keystore, prefs
from jobradar.db import connect
from jobradar.ingest import ingest
from jobradar.match import evaluate, prefilter, set_label
from jobradar.match import runner as matcher
from jobradar.models import Posting
from jobradar.normalize import now_iso
from jobradar.web.app import create_app

AD = "Analyse on-chain and product data with SQL and Python. Remote, worldwide. " * 10


def _job(title, locations=("Remote (Anywhere)",), remote=True, countries=(), scope="anywhere", seniority="mid",
         role="data"):
    return {"title": title, "locations": list(locations), "countries": list(countries), "remote": remote,
            "remote_scope": scope, "seniority": seniority, "role": role}


def test_title_rules_follow_preferences():
    p = prefs.DEFAULTS
    assert prefilter.title_fits(_job("Product Data Analyst"), p)
    assert prefilter.title_fits(_job("Risk Analyst"), p)
    assert not prefilter.title_fits(_job("KYC Analyst"), p)
    assert not prefilter.title_fits(_job("Data Analyst Intern", seniority="intern"), p)
    assert prefilter.title_fits(_job("KYC Analyst"), {**p, "analyst_types": {"compliance_kyc_aml": "maybe"}})
    assert not prefilter.title_fits(_job("Risk Analyst"), {**p, "analyst_types": {"risk_fraud": "no"}})
    no_product = {**p, "other_tracks": {"product": "no"}}
    assert not prefilter.title_fits(_job("Product Manager", role="product"), no_product)
    assert prefilter.title_fits(_job("Product Data Analyst"), no_product)
    backend = _job("Backend Engineer (Python)", role="engineering")
    assert prefilter.title_fits(backend, p)
    assert not prefilter.title_fits(backend, {**p, "other_tracks": {"backend": "no"}})


def test_place_rules_follow_preferences():
    p = prefs.DEFAULTS
    assert prefilter.place(_job("x"), p) == "remote anywhere"
    many = _job("x", [f"Remote ({c})" for c in ("US", "DE", "SG", "BR", "AE")], countries=["US"], scope="restricted")
    assert prefilter.place(many, p) == "remote anywhere"
    germany = _job("x", ["Remote (Germany)"], countries=["DE"], scope="restricted")
    usa = _job("x", ["Remote (United States)"], countries=["US"], scope="restricted")
    assert prefilter.place(germany, p) and not prefilter.place(usa, p)
    assert prefilter.place(usa, {**p, "remote_regions": ["us"]})
    assert not prefilter.place(germany, {**p, "single_country_remote": "hide"})
    london = _job("x", ["London"], remote=False, countries=["GB"], scope=None)
    assert not prefilter.place(london, p)
    assert prefilter.place(london, {**p, "location": "remote_or_uk_office"}) == "UK office"


def _result(**kw):
    base = {"track": "analyst", "analyst_type": "onchain_analytics", "actually_remote": True,
            "must_haves": [{"req": "SQL", "met": "yes", "evidence": "Dune"}], "knockouts": [],
            "scores": {"recruiter": 70, "hiring_manager": 65, "want": 80}, "one_line": "fits",
            "top_risks": ["needs Looker"], "start_from": "Nansen Product Analyst"}
    return {**base, **kw}


@pytest.mark.parametrize("kw, expected", [
    ({}, ("apply_now", None)),
    ({"knockouts": [{"type": "location", "quote": "3 days in our London office"}]}, ("skip", "knockout")),
    ({"knockouts": [{"type": "right_to_work", "quote": "must be authorized to work in the U.S."}]}, ("skip", "knockout")),
    ({"knockouts": [{"type": "years", "quote": "6+ years of product analytics"}]}, ("apply_now", None)),
    ({"actually_remote": False}, ("skip", "knockout")),
    ({"scores": {"recruiter": 90, "hiring_manager": 90, "want": 40}}, ("skip", "low want")),
    ({"track": "backend", "scores": {"recruiter": 50, "hiring_manager": 50, "want": 70}}, ("stretch", None)),
    ({"track": "quant", "scores": {"recruiter": 40, "hiring_manager": 50, "want": 70}}, ("skip", "too far")),
    ({"scores": {"recruiter": 71, "hiring_manager": 72, "want": 58}}, ("tailor_then_apply", None)),
    ({"scores": {"recruiter": 30, "hiring_manager": 40, "want": 75}}, ("stretch", None)),
    ({"scores": {"recruiter": 30, "hiring_manager": 40, "want": 60}}, ("skip", "weak fit")),
])
def test_verdict_rules(kw, expected):
    assert evaluate.verdict(evaluate.clean(_result(**kw))) == expected


def test_clean_drops_bad_values_and_unquoted_knockouts():
    r = evaluate.clean(_result(track="sales", start_from="Made Up CV", scores={"recruiter": "88", "hiring_manager": 120,
                                                                              "want": -5},
                               knockouts=[{"type": "years", "quote": ""}, {"type": "other", "quote": "Use Java 17"},
                                          {"type": "right_to_work", "quote": "US only"}],
                               apply_notes=["Mention the word CANDYSHOP", "", 3, "a", "b", "c"]))
    assert r["track"] == "none" and r["start_from"] is None and r["analyst_type"] is None
    assert r["scores"] == {"recruiter": 88, "hiring_manager": 100, "want": 0}
    assert r["knockouts"] == [{"type": "right_to_work", "quote": "US only"}]
    assert r["top_risks"] == ["Hard ask: “Use Java 17”", "needs Looker"]
    assert r["apply_notes"] == ["Mention the word CANDYSHOP", "3", "a", "b"]
    with pytest.raises(ValueError):
        evaluate.clean({"scores": {"recruiter": 1}})


def test_messages_keep_the_profile_prefix_stable():
    job = {"title": "Data Analyst", "company": "Acme", "locations": [], "place": "remote", "salary": None,
           "posted_at": None, "description": AD}
    a = evaluate.messages(job, prefs.DEFAULTS)
    b = evaluate.messages({**job, "title": "Other"}, {**prefs.DEFAULTS, "hours": "uk_eu"})
    assert a[0] == b[0] and "Candidate profile" in a[0]["content"] and "json" in a[0]["content"]
    assert "Data Analyst" in a[1]["content"] and '"hours": "uk_eu"' in b[1]["content"]


@pytest.fixture
def app_db(tmp_path, monkeypatch):
    monkeypatch.setattr(keystore, "get_key", lambda: ("sk-test0123456789abcdef", "keychain"))
    monkeypatch.setattr(enrich, "_fetch", lambda http, title, urls: (None, "no-url"))
    calls = []

    def fake_chat(key, messages, **kw):
        calls.append(kw["model"])
        return _result(apply_notes=["Mention the word CANDYSHOP"]), {"prompt_cache_hit_tokens": 4000,
                                                                     "prompt_cache_miss_tokens": 1000,
                           "completion_tokens": 3000}

    monkeypatch.setattr(deepseek, "chat_json", fake_chat)
    db = tmp_path / "m.db"
    conn = connect(db)
    ingest(conn, [Posting(source="cryptojobslist", source_job_id=str(i), company=c, title=t, posted_at=now_iso(),
                          locations=["Remote (Anywhere)"], remote=True, description=d) for i, (c, t, d) in enumerate(
        [("Kamino", "Product Data Analyst", AD), ("Dune", "On-chain Analyst", AD), ("Tiny", "Data Analyst", "short"),
         ("Acme", "Sales Executive", AD)])])
    conn.execute("UPDATE companies SET sector = 'crypto'")
    conn.commit()
    ids = dict(conn.execute("SELECT c.name, j.id FROM jobs j JOIN companies c ON c.id = j.company_id").fetchall())
    conn.close()
    return TestClient(create_app(db, sectors_csv=tmp_path / "s.csv")), db, ids, calls


def _wait():
    if matcher._thread:
        matcher._thread.join(10)


def test_run_asks_before_spending_then_scores_in_background(app_db):
    client, db, ids, calls = app_db
    r = client.post("/shortlist/run")
    assert "<b>3</b> of them are new or changed" in r.text and "Score 3 jobs" in r.text and calls == []

    r = client.post("/shortlist/run/start")
    _wait()
    assert calls == ["deepseek-v4-pro", "deepseek-v4-pro"]
    conn = connect(db)
    rows = {r["job_id"]: dict(r) for r in conn.execute("SELECT * FROM match_evaluations")}
    assert rows[ids["Kamino"]]["verdict"] == "apply_now" and rows[ids["Kamino"]]["model"] == "deepseek-v4-pro"
    assert rows[ids["Tiny"]]["verdict"] == "needs_ad" and ids["Acme"] not in rows
    run = matcher.last_run(conn)
    assert (run["status"], run["planned"], run["evaluated"], run["failed"]) == ("done", 3, 3, 0)
    assert run["cost_usd"] > 0

    assert client.get("/shortlist/run/status").headers.get("HX-Refresh") == "true"
    page = client.get("/shortlist").text
    assert "Scored by deepseek-v4-pro" in page and "DeepSeek's notes" in page and "Last run" in page
    assert "To apply</span> Mention the word CANDYSHOP" in page

    r = client.post("/shortlist/run")
    assert "already scored" in r.text


def test_rescoring_keeps_labels_and_follows_preference_changes(app_db):
    client, db, ids, calls = app_db
    client.post("/shortlist/run/start")
    _wait()
    conn = connect(db)
    set_label(conn, ids["Dune"], "N", "not for me")
    prefs.save(conn, {**prefs.current(conn)[0], "hours": "uk_eu"}, "test")
    assert "<b>3</b> of them are new or changed" in client.post("/shortlist/run").text
    client.post("/shortlist/run/start", data={"limit": "1"})
    _wait()
    first = conn.execute("SELECT job_id, label FROM match_evaluations WHERE prefs_version = 1").fetchall()
    assert [tuple(r) for r in first] == [(ids["Dune"], "N")]
    assert "agrees with <b>0 of 1</b>" in client.get("/shortlist").text


def test_already_running_guard(app_db, monkeypatch):
    client, db, _, _ = app_db

    class Alive:
        def is_alive(self):
            return True

    monkeypatch.setattr(matcher, "_thread", Alive())
    with pytest.raises(matcher.AlreadyRunning):
        matcher.start(db, "sk-x")
    assert "already in progress" in client.post("/shortlist/run/start").text


def test_stale_running_row_is_marked_interrupted(app_db, monkeypatch):
    client, db, _, _ = app_db
    monkeypatch.setattr(matcher, "_thread", None)
    conn = connect(db)
    conn.execute("INSERT INTO match_runs (started_at, status, model, planned) VALUES (?, 'running', 'm', 5)",
                 (now_iso(),))
    conn.commit()
    page = client.get("/shortlist").text
    assert "Run matcher" in page and "(interrupted)" in page


def test_run_button_disabled_without_key(app_db, monkeypatch):
    client, *_ = app_db
    monkeypatch.setattr(keystore, "get_key", lambda: (None, "keychain"))
    page = client.get("/shortlist").text
    assert "<button class=\"small\" disabled>Run matcher</button>" in page
    assert "Settings first" in client.post("/shortlist/run/start").text


def test_hand_scored_rows_need_deepseek(app_db):
    _, db, ids, _ = app_db
    conn = connect(db)
    stamp = evaluate.stamps(0)
    job = {"description": AD}
    assert matcher.needs_scoring(None, job, stamp)
    row = {"model": None}
    assert matcher.needs_scoring(row, job, stamp)
    row = {"description_hash": evaluate.digest(AD), **stamp}
    assert not matcher.needs_scoring(row, job, stamp)
    assert matcher.needs_scoring({**row, "prefs_version": 1}, job, stamp)
    assert matcher.needs_scoring(row, {"description": AD + "changed"}, stamp)
    assert json.loads(json.dumps(stamp))["model"] == "deepseek-v4-pro"
