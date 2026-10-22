import json

import pytest
from fastapi.testclient import TestClient

from jobradar import deepseek, keystore, prefs
from jobradar.db import connect
from jobradar.web.app import create_app


def test_validate_keeps_only_known_keys_and_allowed_values():
    out = prefs.validate({"hours": "uk_eu", "nonsense": 1, "token_pay": "maybe later", "fresh_days": 90,
                          "analyst_types": {"risk_fraud": "maybe", "astrology": "yes", "bi_reporting": "sure"},
                          "seniority": ["senior", "boss", "mid"], "dislikes": ["sales quotas", 3, " "]})
    assert out == {"hours": "uk_eu", "fresh_days": 30, "analyst_types": {"risk_fraud": "maybe"},
                   "seniority": ["mid", "senior"], "dislikes": ["sales quotas"]}
    assert prefs.validate({"nonsense": 1}) is None
    assert prefs.validate("not a dict") is None


def test_defaults_focus_on_analyst_and_list_what_is_missing(tmp_path):
    conn = connect(tmp_path / "p.db")
    p, version = prefs.current(conn)
    assert version == 0 and p["focus"] == "analyst"
    missing = prefs.missing(p)
    assert "hours" in missing and "analyst_types.risk_fraud" in missing
    assert "analyst_types.product_data_analytics" not in missing and "dislikes" not in missing


def test_merge_updates_maps_and_replaces_lists():
    p = prefs.merge(prefs.DEFAULTS, {"analyst_types": {"risk_fraud": "no"}, "dislikes": ["quotas"]})
    assert p["analyst_types"] == {"product_data_analytics": "yes", "onchain_analytics": "yes", "risk_fraud": "no"}
    assert p["dislikes"] == ["quotas"]


@pytest.fixture
def chat_client(tmp_path, monkeypatch):
    monkeypatch.setattr(keystore, "get_key", lambda: ("sk-test0123456789abcdef", "keychain"))
    sent = []

    def fake_chat(key, messages, **kw):
        sent.append(messages)
        if messages[-1]["content"].startswith("UK hours"):
            return {"reply": "Got it, UK and EU hours. I've suggested that below.",
                    "changes": {"hours": "uk_eu", "bogus": True}}, {}
        return {"reply": "Hi! Which analyst work interests you?", "changes": None}, {}

    monkeypatch.setattr(deepseek, "chat_json", fake_chat)
    db = tmp_path / "web.db"
    return TestClient(create_app(db, sectors_csv=tmp_path / "s.csv")), db, sent


def test_opening_question_then_proposal_then_apply(chat_client):
    client, db, sent = chat_client
    page = client.get("/preferences")
    assert "not set yet" in page.text and 'hx-trigger="load"' in page.text

    r = client.post("/preferences/chat", data={})
    assert "Which analyst work" in r.text
    assert "Not set yet" in sent[0][0]["content"] and "hours" in sent[0][0]["content"]

    r = client.post("/preferences/chat", data={"text": "UK hours only please"})
    assert "UK hours only please" in r.text and "Proposed change" in r.text
    assert "Working hours: UK / EU hours only" in r.text and "bogus" not in r.text
    assert [m["role"] for m in sent[1][1:]] == ["user", "assistant", "user"]
    assert json.loads(sent[1][2]["content"]) == {"reply": "Hi! Which analyst work interests you?", "changes": None}

    conn = connect(db)
    msg_id = conn.execute("SELECT id FROM pref_messages WHERE status = 'pending'").fetchone()[0]
    assert prefs.current(conn)[0]["hours"] is None
    r = client.post(f"/preferences/proposal/{msg_id}/apply")
    assert "Applied" in r.text and 'hx-swap-oob="true"' in r.text
    p, version = prefs.current(conn)
    assert p["hours"] == "uk_eu" and version == 1
    assert client.post(f"/preferences/proposal/{msg_id}/apply").status_code == 404


def test_discard_leaves_preferences_unchanged(chat_client):
    client, db, _ = chat_client
    client.post("/preferences/chat", data={"text": "UK hours only please"})
    conn = connect(db)
    msg_id = conn.execute("SELECT id FROM pref_messages WHERE status = 'pending'").fetchone()[0]
    r = client.post(f"/preferences/proposal/{msg_id}/discard")
    assert "Discarded" in r.text
    p, version = prefs.current(conn)
    assert version == 0 and p["hours"] is None


def test_new_conversation_clears_the_chat_but_keeps_preferences(chat_client):
    client, db, _ = chat_client
    client.post("/preferences/chat", data={"text": "UK hours only please"})
    r = client.post("/preferences/new")
    assert "getting ready" in r.text
    assert prefs.messages(connect(db)) == []
    assert "UK hours only please" not in client.get("/preferences").text


def test_chat_disabled_without_key(tmp_path, monkeypatch):
    monkeypatch.setattr(keystore, "get_key", lambda: (None, "keychain"))
    client = TestClient(create_app(tmp_path / "web.db", sectors_csv=tmp_path / "s.csv"))
    page = client.get("/preferences")
    assert "Add your DeepSeek API key" in page.text and 'name="text"' not in page.text
    assert "Settings first" in client.post("/preferences/chat", data={"text": "hi"}).text


def test_failed_turn_is_logged_and_keeps_the_typed_text(chat_client, monkeypatch, caplog):
    client, db, _ = chat_client

    def broken(key, messages, **kw):
        raise ValueError("DeepSeek failed 2 times; last problem: reply was not a json object")

    monkeypatch.setattr(deepseek, "chat_json", broken)
    r = client.post("/preferences/chat", data={"text": "BI is a maybe"})
    assert r.headers["X-Chat-Error"] == "1" and "still in the box" in r.text
    assert "'BI is a maybe'" in caplog.text and "not a json object" in caplog.text
    assert prefs.messages(connect(db)) == []
