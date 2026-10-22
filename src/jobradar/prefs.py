import json

from . import deepseek
from .normalize import now_iso

LEVELS = {"yes": "Yes", "maybe": "Maybe", "no": "No"}

# key -> (label, kind, options). kind: choice | map (option -> LEVELS) | multi | bool | int | text | list
SCHEMA = {
    "focus": ("Main focus", "choice", {
        "analyst": "Data analyst", "product": "Product", "research": "Research", "ops_strategy": "Ops & strategy",
        "growth": "Growth"}),
    "analyst_types": ("Analyst work", "map", {
        "product_data_analytics": "Product / data analytics", "onchain_analytics": "On-chain analytics",
        "bi_reporting": "BI & reporting", "token_market_research": "Token & market research",
        "risk_fraud": "Risk & fraud analytics", "compliance_kyc_aml": "Compliance (KYC / AML)",
        "trading_market_ops": "Trading & market-ops analyst"}),
    "other_tracks": ("Other job families", "map", {
        "product": "Product management", "research": "Research", "ops_strategy": "Ops & strategy",
        "growth": "Growth", "quant": "Quant", "backend": "Backend engineering"}),
    "location": ("Where", "choice", {"remote_only": "Remote only", "remote_or_uk_office": "Remote, or a UK office"}),
    "single_country_remote": ("Remote limited to one country", "choice", {
        "show": "Show them", "uk_eu_only": "Only if UK or EU", "hide": "Hide them"}),
    "work_rights": ("Right to work", "text", None),
    "needs_sponsorship": ("Needs visa sponsorship", "bool", None),
    "hours": ("Working hours", "choice", {
        "uk_eu": "UK / EU hours only", "uk_eu_us_east": "Up to US East hours", "any": "Any time zone"}),
    "seniority": ("Levels", "multi", {
        "junior": "Junior", "mid": "Mid", "senior": "Senior", "lead": "Lead", "head": "Head (small teams)"}),
    "min_salary": ("Minimum salary", "text", None),
    "token_pay": ("Pay in tokens", "choice", {
        "ok": "OK", "ok_with_base": "OK on top of a cash base", "no": "Cash only"}),
    "ad_languages": ("Ad languages", "multi", {"en": "English", "zh": "Chinese"}),
    "fresh_days": ("Posted within (days)", "int", (1, 30)),
    "must_haves": ("Must-haves", "list", None),
    "dislikes": ("Dislikes", "list", None),
    "profile_notes": ("Corrections to your profile", "list", None),
}
OPTIONAL = {"must_haves", "dislikes", "profile_notes"}

DEFAULTS = {
    "focus": "analyst",
    "analyst_types": {"product_data_analytics": "yes", "onchain_analytics": "yes"},
    "other_tracks": {},
    "location": "remote_only",
    "single_country_remote": None,
    "work_rights": None,
    "needs_sponsorship": None,
    "hours": None,
    "seniority": None,
    "min_salary": None,
    "token_pay": None,
    "ad_languages": ["en", "zh"],
    "fresh_days": 14,
    "must_haves": [],
    "dislikes": [],
    "profile_notes": [],
}


def current(conn) -> tuple[dict, int]:
    row = conn.execute("SELECT version, data FROM preferences ORDER BY version DESC LIMIT 1").fetchone()
    if not row:
        return json.loads(json.dumps(DEFAULTS)), 0
    return {**json.loads(json.dumps(DEFAULTS)), **json.loads(row["data"])}, row["version"]


def missing(prefs: dict) -> list[str]:
    out = []
    for key, (_, kind, options) in SCHEMA.items():
        if key in OPTIONAL:
            continue
        value = prefs.get(key)
        if kind == "map":
            out += [f"{key}.{k}" for k in options if k not in (value or {})]
        elif value is None:
            out.append(key)
    return out


def _clean(kind: str, options, value):
    if kind == "choice":
        return value if value in options else None
    if kind == "map":
        if not isinstance(value, dict):
            return None
        return {k: v for k, v in value.items() if k in options and v in LEVELS} or None
    if kind == "multi":
        if not isinstance(value, list):
            return None
        return [v for v in options if v in value] or None
    if kind == "bool":
        return value if isinstance(value, bool) else None
    if kind == "int":
        return min(max(value, options[0]), options[1]) if isinstance(value, int) and not isinstance(value, bool) else None
    if kind == "text":
        return value.strip()[:200] if isinstance(value, str) and value.strip() else None
    if kind == "list":
        if not isinstance(value, list):
            return None
        return [v.strip()[:200] for v in value if isinstance(v, str) and v.strip()][:20]


def validate(changes) -> dict | None:
    """Keep only known keys with allowed values. Lists replace the old list; maps merge into the old map."""
    if not isinstance(changes, dict):
        return None
    out = {}
    for key, value in changes.items():
        if key not in SCHEMA:
            continue
        _, kind, options = SCHEMA[key]
        cleaned = _clean(kind, options, value)
        if cleaned is not None or (kind == "list" and value == []):
            out[key] = cleaned if cleaned is not None else []
    return out or None


def merge(prefs: dict, changes: dict) -> dict:
    new = json.loads(json.dumps(prefs))
    for key, value in changes.items():
        new[key] = {**(new.get(key) or {}), **value} if SCHEMA[key][1] == "map" else value
    return new


def save(conn, prefs: dict, source: str) -> int:
    cur = conn.execute("INSERT INTO preferences (data, source, created_at) VALUES (?, ?, ?)",
                       (json.dumps(prefs, ensure_ascii=False, sort_keys=True), source, now_iso()))
    conn.commit()
    return cur.lastrowid


def apply(conn, msg_id: int) -> bool:
    row = conn.execute("SELECT proposal FROM pref_messages WHERE id = ? AND status = 'pending'", (msg_id,)).fetchone()
    if not row:
        return False
    prefs, _ = current(conn)
    save(conn, merge(prefs, json.loads(row["proposal"])), "chat")
    conn.execute("UPDATE pref_messages SET status = 'applied' WHERE id = ?", (msg_id,))
    conn.commit()
    return True


def discard(conn, msg_id: int) -> bool:
    n = conn.execute("UPDATE pref_messages SET status = 'discarded' WHERE id = ? AND status = 'pending'",
                     (msg_id,)).rowcount
    conn.commit()
    return bool(n)


def show(key: str, value) -> str | None:
    """Human text for one preference, or None when it is not set."""
    _, kind, options = SCHEMA[key]
    if value is None or value == [] or value == {}:
        return None
    if kind == "choice":
        return options.get(value, value)
    if kind == "multi":
        return ", ".join(options.get(v, v) for v in value)
    if kind == "bool":
        return "Yes" if value else "No"
    if kind == "list":
        return "; ".join(value)
    return str(value)


def summary(prefs: dict) -> list[dict]:
    rows = []
    for key, (label, kind, options) in SCHEMA.items():
        value = prefs.get(key)
        if kind == "map":
            value = value or {}
            rows.append({"label": label, "levels": [(name, LEVELS.get(value.get(k))) for k, name in options.items()]})
        else:
            rows.append({"label": label, "value": show(key, value), "optional": key in OPTIONAL})
    return rows


def describe_change(changes: dict) -> list[str]:
    out = []
    for key, value in changes.items():
        label, kind, options = SCHEMA[key]
        if kind == "map":
            out += [f"{options[k]}: {LEVELS[v]}" for k, v in value.items()]
        else:
            out.append(f"{label}: {show(key, value) or 'cleared'}")
    return out


def schema_for_prompt() -> str:
    lines = []
    for key, (label, kind, options) in SCHEMA.items():
        if kind in ("choice", "multi"):
            spec = f"{kind}, one of {list(options)}" if kind == "choice" else f"list, any of {list(options)}"
        elif kind == "map":
            spec = f"object mapping any of {list(options)} to one of {list(LEVELS)}"
        elif kind == "int":
            spec = f"integer {options[0]}-{options[1]}"
        elif kind == "list":
            spec = "list of short strings (send the complete new list)"
        else:
            spec = {"bool": "true or false", "text": "short string"}[kind]
        lines.append(f"- {key} ({label}): {spec}")
    return "\n".join(lines)


HISTORY = 20
OPENED = "(David just opened the Preferences page.)"


def messages(conn) -> list[dict]:
    """The current conversation: everything after the last 'new conversation' divider."""
    start = conn.execute("SELECT COALESCE(MAX(id), 0) FROM pref_messages WHERE role = 'divider'").fetchone()[0]
    return [dict(r) for r in conn.execute("SELECT * FROM pref_messages WHERE id > ? ORDER BY id", (start,))]


def _add(conn, role: str, content: str, proposal: dict | None = None) -> dict:
    cur = conn.execute("INSERT INTO pref_messages (role, content, proposal, status, created_at) VALUES (?, ?, ?, ?, ?)",
                       (role, content, json.dumps(proposal, ensure_ascii=False) if proposal else None,
                        "pending" if proposal else None, now_iso()))
    conn.commit()
    return dict(conn.execute("SELECT * FROM pref_messages WHERE id = ?", (cur.lastrowid,)).fetchone())


def new_conversation(conn) -> None:
    _add(conn, "divider", "")


def reply(conn, key: str, prompt: str, text: str) -> list[dict]:
    """Send David's message (or, when empty, the page-opened cue) to DeepSeek; store and return the new messages."""
    prefs, _ = current(conn)
    system = (f"{prompt}\n\n## Preference fields\n{schema_for_prompt()}\n\n"
              f"## Current preferences (json)\n{json.dumps(prefs, ensure_ascii=False)}\n\n"
              f"## Not set yet\n{', '.join(missing(prefs)) or 'nothing, everything is set'}")
    history = [{"role": m["role"], "content": m["content"]} for m in messages(conn)][-HISTORY:]
    history.append({"role": "user", "content": text or OPENED})
    if history[0]["role"] != "user":
        history.insert(0, {"role": "user", "content": OPENED})
    data, _ = deepseek.chat_json(key, [{"role": "system", "content": system}, *history])
    answer = str(data.get("reply") or "").strip() or "Sorry, I didn't catch that. Could you say it another way?"
    new = [_add(conn, "user", text)] if text else []
    return new + [_add(conn, "assistant", answer, validate(data.get("changes")))]
