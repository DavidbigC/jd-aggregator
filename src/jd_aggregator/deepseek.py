import httpx

BASE = "https://api.deepseek.com"


def balance(key: str) -> dict:
    """Only the Settings key check uses DeepSeek now; Claude does the LLM work."""
    r = httpx.get(f"{BASE}/user/balance", headers={"Authorization": f"Bearer {key}"}, timeout=15)
    r.raise_for_status()
    return r.json()
