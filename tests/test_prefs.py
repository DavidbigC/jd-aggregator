from fastapi.testclient import TestClient

from jd_aggregator import prefs
from jd_aggregator.db import connect
from jd_aggregator.web.app import create_app


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


def test_update_saves_a_new_version_of_valid_changes_only(tmp_path):
    conn = connect(tmp_path / "p.db")
    changes, version = prefs.update(conn, {"hours": "uk_eu", "bogus": True, "analyst_types": {"risk_fraud": "maybe"}})
    assert changes == ["Working hours: UK / EU hours only", "Risk & fraud analytics: Maybe"] and version == 1
    p, _ = prefs.current(conn)
    assert p["hours"] == "uk_eu" and p["analyst_types"]["product_data_analytics"] == "yes"
    assert conn.execute("SELECT source FROM preferences").fetchone()[0] == "claude"
    assert prefs.update(conn, {"bogus": 1}) == ([], 1)


def test_preferences_page_is_read_only(tmp_path):
    client = TestClient(create_app(tmp_path / "web.db", sectors_csv=tmp_path / "s.csv"))
    page = client.get("/preferences").text
    assert "not set yet" in page and "tell Claude in Claude Code" in page and 'name="text"' not in page
    assert client.post("/preferences/chat", data={"text": "hi"}).status_code == 404
