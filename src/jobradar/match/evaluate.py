import hashlib
import json
import re

from .. import deepseek
from ..config import ROOT
from . import priority

MODEL = "deepseek-v4-pro"
PROFILE = ROOT / "seeds" / "candidate_profile.md"
PROMPT = ROOT / "seeds" / "match_prompt.md"
TRACKS = ("analyst", "product", "research", "ops_strategy", "growth", "quant", "backend", "none")
ANALYST_TYPES = ("product_data_analytics", "onchain_analytics", "bi_reporting", "token_market_research", "risk_fraud",
                 "compliance_kyc_aml", "trading_market_ops")
KNOCKOUTS = ("right_to_work", "location", "language", "licence")
MET = ("yes", "partial", "no")
CVS = re.search(r"Use exactly one of these names, or null:\n(.+)\n", PROMPT.read_text()).group(1).split("; ")
SCORES = ("recruiter", "hiring_manager", "want")


def digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:12]


def stamps(prefs_version: int) -> dict:
    return {"model": MODEL, "prompt_version": digest(PROMPT.read_text()), "profile_hash": digest(PROFILE.read_text()),
            "prefs_version": prefs_version}


def messages(job: dict, prefs: dict) -> list[dict]:
    """Profile and prompt first and byte-stable, then preferences, so DeepSeek's prefix cache covers all three."""
    ad = (f"## David's preferences (json)\n{json.dumps(prefs, ensure_ascii=False, sort_keys=True)}\n\n"
          f"## Job\nTitle: {job['title']}\nCompany: {job['company']}\n"
          f"Locations: {' / '.join(job['locations']) or 'not given'}\nJob board's remote label: {job['place']}\n"
          f"Salary: {job['salary'] or 'not given'}\nPosted: {(job['posted_at'] or '')[:10] or 'unknown'}\n\n"
          f"### Full ad\n{job['description']}")
    return [{"role": "system", "content": f"{PROFILE.read_text()}\n\n{PROMPT.read_text()}"},
            {"role": "user", "content": ad}]


def _text(x, limit=300) -> str:
    return str(x).strip()[:limit] if isinstance(x, (str, int, float)) and str(x).strip() else ""


def _texts(x, n=8) -> list[str]:
    return [t for t in (_text(i, 200) for i in (x if isinstance(x, list) else [])) if t][:n]


def clean(data: dict) -> dict:
    """Validate DeepSeek's JSON; raise ValueError when the scores are unusable."""
    scores = data.get("scores") or {}
    try:
        s = {k: min(100, max(0, round(float(scores[k])))) for k in SCORES}
    except (KeyError, TypeError, ValueError):
        raise ValueError(f"missing or bad scores: {scores!r}"[:300])
    track = data.get("track") if data.get("track") in TRACKS else "none"
    quoted = [k for k in data.get("knockouts") or [] if isinstance(k, dict) and _text(k.get("quote"))]
    knockouts = [{"type": k["type"], "quote": _text(k["quote"])} for k in quoted if k.get("type") in KNOCKOUTS]
    # Years, skills and anything else are gaps, not eligibility: show them as risks so the job isn't hidden.
    hard_asks = [f"Hard ask: “{_text(k['quote'], 150)}”" for k in quoted if k.get("type") not in KNOCKOUTS]
    return {
        "track": track,
        "analyst_type": data.get("analyst_type") if track == "analyst" and data.get("analyst_type") in ANALYST_TYPES
        else None,
        "actually_remote": data.get("actually_remote") is not False,
        "must_haves": [{"req": _text(m.get("req"), 200), "met": m.get("met") if m.get("met") in MET else "no",
                        "evidence": _text(m.get("evidence"), 200)}
                       for m in data.get("must_haves") or [] if isinstance(m, dict) and _text(m.get("req"))][:8],
        "nice_to_haves": _texts(data.get("nice_to_haves")),
        "knockouts": knockouts,
        "scores": s,
        "one_line": _text(data.get("one_line")),
        "top_risks": (hard_asks + _texts(data.get("top_risks"), 4))[:4],
        "start_from": data.get("start_from") if data.get("start_from") in CVS else None,
        "lead_with": _texts(data.get("lead_with"), 5),
        "mirror_keywords": _texts(data.get("mirror_keywords"), 10),
        "interview_prep": _texts(data.get("interview_prep"), 5),
        "questions_for_recruiter": _texts(data.get("questions_for_recruiter"), 5),
        "apply_notes": _texts(data.get("apply_notes"), 4),
    }


def verdict(r: dict) -> tuple[str, str | None]:
    """The verdict rules, applied in order. Want leads: a job David wants and could do is shown even when the
    recruiter score is low, because the tailored CV is what gets David past the screen."""
    a, b, c = (r["scores"][k] for k in SCORES)
    if r["knockouts"] or not r["actually_remote"]:
        return "skip", "knockout"
    if c < 45:
        return "skip", "low want"
    if r["track"] in ("backend", "quant"):
        return ("stretch", None) if b >= 40 else ("skip", "too far")
    if c >= 65 and b >= 60 and a >= 50:
        return "apply_now", None
    if (c >= 55 and b >= 45) or (a >= 45 and b >= 50):
        return "tailor_then_apply", None
    if c >= 55 and b >= 35:
        return "stretch", None
    return "skip", "weak fit"


def rescore(conn) -> dict[str, int]:
    """Re-derive every verdict and priority from the stored scores, without calling DeepSeek. Labels are kept."""
    moved: dict[str, int] = {}
    for row in conn.execute("SELECT job_id, verdict, rec, hm, want, result FROM match_evaluations "
                            "WHERE rec IS NOT NULL").fetchall():
        v, reason = row["verdict"], None
        if row["result"] and v != "needs_ad":
            v, reason = verdict(json.loads(row["result"]))
            if v != row["verdict"]:
                key = f"{row['verdict']} → {v}"
                moved[key] = moved.get(key, 0) + 1
            conn.execute("UPDATE match_evaluations SET verdict = ?, reason = ? WHERE job_id = ?",
                         (v, reason, row["job_id"]))
        conn.execute("UPDATE match_evaluations SET priority = ? WHERE job_id = ?",
                     (priority(row["rec"], row["hm"], row["want"]), row["job_id"]))
    conn.commit()
    return moved


def evaluate(key: str, job: dict, prefs: dict, stamp: dict) -> tuple[dict, dict]:
    """Score one job. Returns the row for import_results and DeepSeek's token usage."""
    data, usage = deepseek.chat_json(key, messages(job, prefs), model=MODEL, thinking=True, max_tokens=16000)
    r = clean(data)
    v, reason = verdict(r)
    knock = "; ".join(f"“{k['quote']}”" for k in r["knockouts"][:2])
    risk = "; ".join(([f"Knockout: {knock}"] if knock else []) + r["top_risks"][:2])
    return {"job_id": job["id"], "verdict": v, "reason": reason, "track": r["track"],
            "rec": r["scores"]["recruiter"], "hm": r["scores"]["hiring_manager"], "want": r["scores"]["want"],
            "why": r["one_line"], "risk": risk or None, "start_cv": r["start_from"],
            "description_hash": digest(job["description"] or ""), "result": json.dumps(r, ensure_ascii=False),
            **stamp}, usage
