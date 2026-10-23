import json
import logging
import time

import httpx

BASE = "https://api.deepseek.com"
CHAT_MODEL = "deepseek-flash"
TRIES = 2
log = logging.getLogger(__name__)


def _auth(key: str) -> dict:
    return {"Authorization": f"Bearer {key}"}


def balance(key: str) -> dict:
    r = httpx.get(f"{BASE}/user/balance", headers=_auth(key), timeout=15)
    r.raise_for_status()
    return r.json()


def chat_json(key: str, messages: list[dict], model: str = CHAT_MODEL, thinking: bool = False,
              max_tokens: int = 2000, timeout: float = 180) -> tuple[dict, dict]:
    """One JSON-mode completion. Dropped connections and empty or non-JSON replies are retried once."""
    body = {"model": model, "messages": messages, "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
            "thinking": {"type": "enabled" if thinking else "disabled"}}
    problem = ""
    for attempt in range(1, TRIES + 1):
        start = time.monotonic()
        try:
            r = httpx.post(f"{BASE}/chat/completions", json=body, headers=_auth(key), timeout=timeout)
        except httpx.TransportError as e:
            problem = f"{type(e).__name__}: {e}"
            log.warning("%s attempt %d/%d failed after %.1fs: %s", model, attempt, TRIES, time.monotonic() - start, problem)
            continue
        if r.status_code >= 400:
            log.error("%s attempt %d/%d: HTTP %d %s", model, attempt, TRIES, r.status_code, r.text[:300])
        r.raise_for_status()
        data = r.json()
        choice, usage = data["choices"][0], data.get("usage", {})
        content = choice["message"].get("content") or ""
        log.info("%s attempt %d: %.1fs, finish=%s, tokens in %s (cached %s) out %s", model, attempt,
                 time.monotonic() - start, choice.get("finish_reason"), usage.get("prompt_tokens"),
                 usage.get("prompt_cache_hit_tokens"), usage.get("completion_tokens"))
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, dict):
            return parsed, usage
        problem = f"reply was not a json object (finish={choice.get('finish_reason')}): {content[:300]!r}"
        log.warning("%s attempt %d/%d: %s", model, attempt, TRIES, problem)
    raise ValueError(f"DeepSeek failed {TRIES} times; last problem: {problem}")
