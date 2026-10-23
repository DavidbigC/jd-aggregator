import httpx
import pytest
from fastapi.testclient import TestClient

from jd_aggregator import deepseek, keystore
from jd_aggregator.web.app import create_app

GOOD = "sk-0123456789abcdef0123456789abcdef"


@pytest.fixture
def store(monkeypatch):
    """In-memory stand-in for the Keychain; DeepSeek accepts only GOOD."""
    s = {"key": None, "source": "keychain"}
    monkeypatch.setattr(keystore, "get_key", lambda: (s["key"], s["source"]))
    monkeypatch.setattr(keystore, "set_key", lambda k: s.update(key=k))
    monkeypatch.setattr(keystore, "delete_key", lambda: s.update(key=None))

    def balance(key):
        if key != GOOD:
            raise httpx.HTTPStatusError("401", request=httpx.Request("GET", "x"), response=httpx.Response(401))
        return {"is_available": True, "balance_infos": [{"currency": "USD", "total_balance": "4.20"}]}

    monkeypatch.setattr(deepseek, "balance", balance)
    return s


@pytest.fixture
def client(tmp_path, store):
    return TestClient(create_app(tmp_path / "web.db", sectors_csv=tmp_path / "s.csv"))


def test_settings_page_without_key(client):
    r = client.get("/settings")
    assert r.status_code == 200
    assert 'name="key"' in r.text and "Settings" in r.text


def test_save_good_key_stores_it_and_shows_balance(client, store):
    r = client.post("/settings/deepseek", data={"key": GOOD})
    assert store["key"] == GOOD
    assert "Connected" in r.text and "…cdef" in r.text and "USD 4.20" in r.text
    assert GOOD not in r.text


def test_rejected_key_is_not_stored(client, store):
    r = client.post("/settings/deepseek", data={"key": "sk-ffffffffffffffffffffffff"})
    assert store["key"] is None
    assert "rejected this key (401)" in r.text


def test_malformed_key_is_refused(client, store):
    r = client.post("/settings/deepseek", data={"key": "hello world"})
    assert store["key"] is None
    assert "look like a DeepSeek key" in r.text


def test_remove_asks_then_clears(client, store):
    store["key"] = GOOD
    r = client.post("/settings/deepseek/delete")
    assert "Remove the key?" in r.text and store["key"] == GOOD
    r = client.post("/settings/deepseek/delete", data={"confirm": "1"})
    assert store["key"] is None and 'name="key"' in r.text


def test_env_key_hides_remove(client, store):
    store.update(key=GOOD, source="env")
    r = client.post("/settings/deepseek/test")
    assert "DEEPSEEK_API_KEY" in r.text and "Remove key" not in r.text and "USD 4.20" in r.text
