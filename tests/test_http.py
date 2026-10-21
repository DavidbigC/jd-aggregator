import httpx
import pytest

from jobradar.http import Http


def _client(statuses, monkeypatch):
    monkeypatch.setattr("jobradar.http.time.sleep", lambda s: None)
    calls = []

    def handler(request):
        calls.append(str(request.url))
        return httpx.Response(statuses[min(len(calls), len(statuses)) - 1], json={"ok": True})

    return Http(min_interval=0, transport=httpx.MockTransport(handler)), calls


def test_retries_on_503_then_succeeds(monkeypatch):
    http, calls = _client([503, 200], monkeypatch)
    assert http.get("https://example.com/x").json() == {"ok": True}
    assert len(calls) == 2


def test_404_raises_without_retry(monkeypatch):
    http, calls = _client([404], monkeypatch)
    with pytest.raises(httpx.HTTPStatusError):
        http.get("https://example.com/x")
    assert len(calls) == 1


def test_gives_up_after_three_attempts(monkeypatch):
    http, calls = _client([503], monkeypatch)
    with pytest.raises(httpx.HTTPStatusError):
        http.get("https://example.com/x")
    assert len(calls) == 3
