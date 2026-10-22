import logging

import httpx
import pytest

from jobradar import deepseek


def _reply(content, finish="stop"):
    return httpx.Response(200, json={"choices": [{"message": {"content": content}, "finish_reason": finish}],
                                     "usage": {"prompt_tokens": 10, "completion_tokens": 5}})


@pytest.fixture
def replies(monkeypatch):
    queue = []

    def post(*a, **k):
        item = queue.pop(0)
        if isinstance(item, Exception):
            raise item
        item.request = httpx.Request("POST", a[0])
        return item

    monkeypatch.setattr(deepseek.httpx, "post", post)
    return queue


def test_non_json_reply_is_retried(replies, caplog):
    replies += [_reply('{"reply": "cut off', finish="length"), _reply('{"reply": "ok", "changes": null}')]
    with caplog.at_level(logging.INFO, logger="jobradar.deepseek"):
        data, usage = deepseek.chat_json("sk-x", [])
    assert data == {"reply": "ok", "changes": None} and usage["completion_tokens"] == 5
    assert "not a json object (finish=length)" in caplog.text and "attempt 2" in caplog.text


def test_dropped_connection_is_retried(replies, caplog):
    replies += [httpx.ReadTimeout("timed out"), _reply('{"reply": "ok"}')]
    with caplog.at_level(logging.INFO, logger="jobradar.deepseek"):
        assert deepseek.chat_json("sk-x", [])[0] == {"reply": "ok"}
    assert "ReadTimeout" in caplog.text


def test_two_bad_replies_raise_with_the_reason(replies):
    replies += [_reply(""), _reply("[1, 2]")]
    with pytest.raises(ValueError, match=r"failed 2 times.*\[1, 2\]"):
        deepseek.chat_json("sk-x", [])


def test_http_errors_are_not_retried(replies, caplog):
    replies += [httpx.Response(402, text="Insufficient Balance")]
    with pytest.raises(httpx.HTTPStatusError):
        deepseek.chat_json("sk-x", [])
    assert "HTTP 402 Insufficient Balance" in caplog.text and not replies
