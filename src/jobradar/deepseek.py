import json

import httpx

BASE = "https://api.deepseek.com"
CHAT_MODEL = "deepseek-flash"


def _auth(key: str) -> dict:
    return {"Authorization": f"Bearer {key}"}


def balance(key: str) -> dict:
    r = httpx.get(f"{BASE}/user/balance", headers=_auth(key), timeout=15)
    r.raise_for_status()
    return r.json()


def chat_json(key: str, messages: list[dict], model: str = CHAT_MODEL, thinking: bool = False,
              max_tokens: int = 2000) -> tuple[dict, dict]:
    """One JSON-mode completion. DeepSeek documents occasional empty content, so it is retried once."""
    body = {"model": model, "messages": messages, "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
            "thinking": {"type": "enabled" if thinking else "disabled"}}
    for _ in range(2):
        r = httpx.post(f"{BASE}/chat/completions", json=body, headers=_auth(key), timeout=180)
        r.raise_for_status()
        data = r.json()
        content = data["choices"][0]["message"].get("content") or ""
        if content.strip():
            return json.loads(content), data.get("usage", {})
    raise ValueError("DeepSeek returned an empty reply twice")
