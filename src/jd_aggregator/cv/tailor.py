import json
import re

from .. import deepseek
from ..config import ROOT
from ..match.evaluate import digest
from . import sources

MODEL = "deepseek-v4-pro"
NAME = "David Chen"
WRITER = ROOT / "seeds" / "cv_writer_prompt.md"
REVIEW = ROOT / "seeds" / "cv_review_prompt.md"
LANGS = ("en", "zh", "zh-Hant")
HEADINGS = {
    "en": ("Summary", "Core Skills", "Experience", "Selected Projects", "Additional Highlights", "Education"),
    "zh": ("个人简介", "核心技能", "工作经历", "精选项目", "其他亮点", "教育背景"),
    "zh-Hant": ("個人簡介", "核心技能", "工作經歷", "精選項目", "其他亮點", "教育背景"),
}
NOTE_KEYS = ("must_haves", "lead_with", "mirror_keywords", "top_risks", "apply_notes")
PRONOUN = re.compile(r"\b(he|she|his|him|her|hers)\b|(?<!其)他(?!们|們)|她", re.I)
MERGED = re.compile(r"(?<!not )(?<!never )\bmerged\b|已合并|已合併", re.I)
HEDGE = re.compile(r"not merged|without merge|team result|exposure to|团队成果|團隊成果", re.I)
TRADER = re.compile(r"\btraders?\b|交易员|交易員", re.I)
STALE = re.compile(r"\bpresent\b|\bcurrent(ly)?\b|至今|现任|現任|目前", re.I)
# Figures worth checking for repeats: percentages, 1M+/10K-style counts, and numbers of 3+ digits that aren't years.
FIGURE = re.compile(r"(?<![\w.$])(\d[\d,.]*(?:%|[KkMm]\+?|\+)|\d{1,3}(?:,\d{3})+|\d{3,})(?![\w%])", re.A)
CJK = re.compile(r"[\u3400-\u9fff]")
AD_YEARS = re.compile(r"(\d{1,2})\s*\+?\s*(?:years|yrs|年)", re.I)
FIVE_YEARS = re.compile(r"\b5\s*\+?\s*(?:years|yrs)|5\s*\+?\s*年", re.I)
MAX_WORDS, MAX_CJK, MAX_SKILL_WORDS = 950, 1800, 5


def stamps() -> dict:
    return {"model": MODEL, "prompt_version": digest(WRITER.read_text() + REVIEW.read_text()),
            "sources_hash": digest(sources.PACK.read_text())}


def _plain(x, limit: int) -> str:
    if not isinstance(x, (str, int, float)):
        return ""
    return re.sub(r"\*\*|__|`|^[-•*]\s+", "", str(x).strip())[:limit].strip()


def _plains(x, n: int, limit: int = 300) -> list[str]:
    return [t for t in (_plain(i, limit) for i in (x if isinstance(x, list) else [])) if t][:n]


def _dicts(x, n: int) -> list[dict]:
    return [d for d in (x if isinstance(x, list) else []) if isinstance(d, dict)][:n]


def clean_cv(data: dict) -> dict:
    """Validate DeepSeek's CV JSON and cap its lengths; raise ValueError when it has no experience."""
    experience = [{"org": _plain(e.get("org"), 80), "title": _plain(e.get("title"), 80),
                   "dates": _plain(e.get("dates"), 60), "bullets": _plains(e.get("bullets"), 5)}
                  for e in _dicts(data.get("experience"), 6)]
    # "Independent | Independent On-Chain Market Maker…" reads as a stutter: keep the title alone as the heading.
    experience = [{**e, "org": e["title"], "title": ""} if e["title"].lower().startswith(e["org"].lower()) else e
                  for e in experience if e["org"] and e["bullets"]]
    if not experience:
        raise ValueError("the CV has no experience entries")
    return {
        "language": data.get("language") if data.get("language") in LANGS else "en",
        "headline": _plain(data.get("headline"), 140),
        "summary": _plain(data.get("summary"), 800),
        "skills": [{"group": _plain(g.get("group"), 50), "items": _plains(g.get("items"), 12, 80)}
                   for g in _dicts(data.get("skills"), 5) if _plain(g.get("group"), 50)],
        "experience": experience,
        "projects": [{"name": _plain(p.get("name"), 100), "dates": _plain(p.get("dates"), 40),
                      "link": _plain(p.get("link"), 200) if str(p.get("link") or "").startswith("http") else None,
                      "bullets": _plains(p.get("bullets"), 3)}
                     for p in _dicts(data.get("projects"), 4) if _plain(p.get("name"), 100)],
        "highlights": _plains(data.get("highlights"), 4),
        "education": [{"degree": _plain(e.get("degree"), 120), "school": _plain(e.get("school"), 80),
                       "year": _plain(e.get("year"), 20)} for e in _dicts(data.get("education"), 3)],
        "notes": _plain(data.get("notes"), 800),
    }


def clean_review(data: dict) -> dict:
    try:
        score = min(100, max(0, round(float(data["score"]))))
    except (KeyError, TypeError, ValueError):
        raise ValueError(f"review has no usable score: {data.get('score')!r}"[:200])
    if _plains(data.get("invented_claims"), 8):
        score = min(score, 40)
    issues = [{"severity": i.get("severity") if i.get("severity") in ("must_fix", "should_fix") else "should_fix",
               "where": _plain(i.get("where"), 80), "problem": _plain(i.get("problem"), 300),
               "fix": _plain(i.get("fix"), 400)} for i in _dicts(data.get("issues"), 10) if _plain(i.get("problem"), 300)]
    return {"score": score, "would_shortlist": score >= 70, "verdict": _plain(data.get("verdict"), 250),
            "issues": sorted(issues, key=lambda i: i["severity"] != "must_fix"),
            "missing_keywords": _plains(data.get("missing_keywords"), 10, 60),
            "invented_claims": _plains(data.get("invented_claims"), 8)}


def _strings(x) -> list[str]:
    if isinstance(x, dict):
        return [s for v in x.values() for s in _strings(v)]
    if isinstance(x, list):
        return [s for v in x for s in _strings(v)]
    return [x] if isinstance(x, str) else []


def _length(text: str) -> tuple[int, int]:
    """(English words, CJK characters)."""
    cjk = len(CJK.findall(text))
    return len(CJK.sub(" ", text).split()), cjk


def _repeated_figures(cv: dict) -> list[str]:
    """Figures that appear in two places across experience entries, projects and highlights (the summary may repeat)."""
    places = [" ".join(e["bullets"]) for e in cv["experience"]] + [" ".join(p["bullets"]) for p in cv["projects"]]
    places.append(" ".join(cv["highlights"]))
    seen: dict[str, int] = {}
    for text in places:
        for f in {m.group(1).rstrip(".,") for m in FIGURE.finditer(text)}:
            if not re.fullmatch(r"(19|20)\d\d", f):
                seen[f] = seen.get(f, 0) + 1
    return sorted(f for f, n in seen.items() if n > 1)


def problems(cv: dict, ad: str = "") -> list[str]:
    """Rule breaks the code can see. Truth is the recruiter pass's job. `ad` is the job message, for the years ask."""
    text = "\n".join(_strings({k: v for k, v in cv.items() if k != "notes"}))
    found = []
    if sources.EMAIL.search(text):
        found.append("it contains an email address")
    if sources.PHONE.search(text):
        found.append("it contains a phone number")
    if amounts := sources.money(text):
        found.append(f"it contains dollar amounts ({', '.join(amounts[:3])}); only 'above $1M volume' is allowed")
    if m := PRONOUN.search(text):
        found.append(f"it uses the pronoun '{m.group(0)}' for David; start bullets with a verb instead")
    if MERGED.search(text):
        found.append("it calls the Spellbook/DefiLlama PRs merged; they were submitted and closed without merge")
    if m := HEDGE.search(text):
        found.append(f"it sells against David with '{m.group(0)}'; state what David has, without hedges")
    heads = " ".join([cv["headline"]] + [f"{e['org']} {e['title']}" for e in cv["experience"]])
    if TRADER.search(heads):
        found.append("it calls David a trader; David is a market maker and arbitrageur")
    orgs = " ".join(f"{e['org']} {e['title']}" for e in cv["experience"]).lower()
    for name, words in (("Independent On-Chain Market Maker & Arbitrageur", ("independent", "独立", "獨立")),
                        ("FLOKI", ("floki",)), ("Elfin Metaverse (Dragon Race)", ("dragon race", "elfin"))):
        if not any(w in orgs for w in words):
            found.append(f"the {name} role is missing from experience")
    for e in cv["experience"]:
        if "floki" in e["org"].lower() and (STALE.search(e["dates"]) or STALE.search(" ".join(e["bullets"]))):
            found.append("it shows FLOKI as current; David left FLOKI in April 2026 (Dec 2024 – Apr 2026, past tense)")
    if re.search(r"(\bcurrent|现任|目前)[^.。;]{0,30}FLOKI|FLOKI[^.。;]{0,30}\bcurrent", cv["summary"], re.I):
        found.append("the summary calls FLOKI current; David left FLOKI in April 2026")
    long_skills = [i for g in cv["skills"] for i in g["items"]
                   if len(re.sub(r"\([^)]*\)|（[^）]*）", "", i).split()) > MAX_SKILL_WORDS
                   or len(CJK.findall(re.sub(r"（[^）]*）|\([^)]*\)", "", i))) > 12]
    if long_skills:
        found.append(f"skills must be tools or methods of at most 4 words, not sentences: {'; '.join(long_skills[:3])}")
    if repeats := _repeated_figures(cv):
        found.append(f"these figures appear in two places, keep each once: {', '.join(repeats[:5])}")
    asked = max((int(n) for n in AD_YEARS.findall(ad) if int(n) <= 15), default=0)
    if asked > 5 and FIVE_YEARS.search(text):
        found.append(f"it states 5+ years while the ad asks for {asked}+; leave years out and let the dates speak")
    words, cjk = _length(text)
    if cjk > MAX_CJK or (cjk < 200 and words > MAX_WORDS):
        found.append(f"it is too long ({cjk} Chinese characters)" if cjk > MAX_CJK else
                     f"it is too long ({words} words); cut to about 850 words")
    return found


def job_message(job: dict, notes: dict | None) -> str:
    text = (f"## Job\nTitle: {job['title']}\nCompany: {job['company']}\n"
            f"Locations: {' / '.join(job['locations']) or 'not given'}\n\n### Full ad\n{job['description']}")
    if notes:
        text += ("\n\n## Matcher notes (json)\n"
                 + json.dumps({k: notes.get(k) for k in NOTE_KEYS if notes.get(k)}, ensure_ascii=False))
    return text


def _system(prompt) -> str:
    """The source pack first and byte-stable, so DeepSeek's prefix cache covers it in every pass."""
    return f"{sources.PACK.read_text()}\n\n{prompt.read_text()}"


def _call(key: str, messages: list[dict]) -> tuple[dict, dict]:
    return deepseek.chat_json(key, messages, model=MODEL, thinking=True, max_tokens=16000, timeout=300)


def _write(key: str, user: str, usage: list[dict]) -> dict:
    """One writer or reviser pass, retried once with the rule breaks named."""
    messages = [{"role": "system", "content": _system(WRITER)}, {"role": "user", "content": user}]
    data, u = _call(key, messages)
    usage.append(u)
    cv = clean_cv(data)
    if found := problems(cv, user):
        messages += [{"role": "assistant", "content": json.dumps(data, ensure_ascii=False)},
                     {"role": "user", "content": "Your CV breaks these rules: " + "; ".join(found)
                      + ". Return the whole corrected CV as the same json object."}]
        data, u = _call(key, messages)
        usage.append(u)
        cv = clean_cv(data)
        if found := problems(cv, user):
            raise ValueError("the CV still breaks the rules: " + "; ".join(found))
    return cv


def _review(key: str, ad: str, cv: dict, usage: list[dict]) -> dict:
    """The writer's notes are for David, not part of the CV, so the screener never sees them."""
    shown = json.dumps({k: v for k, v in cv.items() if k != "notes"}, ensure_ascii=False)
    data, u = _call(key, [{"role": "system", "content": _system(REVIEW)},
                          {"role": "user", "content": f"{ad}\n\n## CV (json)\n{shown}"
                                                      "\n\nReview this CV for this job."}])
    usage.append(u)
    return clean_review(data)


def _revise(key: str, ad: str, cv: dict, review: dict, usage: list[dict]) -> dict:
    return _write(key, f"{ad}\n\n## Your draft (json)\n{json.dumps(cv, ensure_ascii=False)}\n\n"
                       f"## Recruiter review (json)\n{json.dumps(review, ensure_ascii=False)}\n\n"
                       "Revise the CV using this review.", usage)


def _needs_repair(review: dict) -> bool:
    return bool(review["invented_claims"]) or any(i["severity"] == "must_fix" for i in review["issues"])


def tailor(key: str, job: dict, notes: dict | None, stage=lambda s: None) -> dict:
    """Writer → review → revision → screen of the final; when the screen finds an invented claim or a must_fix,
    one repair revision and a second screen. Returns each result and all usage."""
    usage: list[dict] = []
    ad = job_message(job, notes)
    stage("writing")
    draft = _write(key, ad + "\n\nWrite David's CV for this job.", usage)
    stage("reviewing")
    review = _review(key, ad, draft, usage)
    stage("revising")
    final = _revise(key, ad, draft, review, usage)
    stage("checking")
    final_review = _review(key, ad, final, usage)
    if _needs_repair(final_review):
        stage("revising")
        try:
            repaired = _revise(key, ad, final, final_review, usage)
        except ValueError:
            repaired = None  # the repair broke a code rule twice; keep the screened version
        if repaired:
            stage("checking")
            final, final_review = repaired, _review(key, ad, repaired, usage)
    return {"draft": draft, "review": review, "final": final, "final_review": final_review, "usage": usage}


def filename(job: dict) -> str:
    return re.sub(r'[\\/:*?"<>|]+', " ", f"{NAME} - {job['company']} {job['title']}").strip()[:120]


def to_markdown(cv: dict, contact: str, links: list[tuple[str, str]]) -> str:
    """The CV in the devmaster-cv Markdown layout, ready for md-to-pdf with resume.css."""
    h = HEADINGS[cv["language"]]
    head = [f"# {NAME}", "", f"**{cv['headline']}**" if cv["headline"] else ""]
    contact_line = "  \n".join(x for x in (contact, " | ".join(f"[{k}]({u})" for k, u in links)) if x)
    out = head + ["", contact_line, "", f"## {h[0]}", "", cv["summary"], "", f"## {h[1]}", ""]
    out += [f"**{g['group']}:** {', '.join(g['items'])}\n" for g in cv["skills"]]
    out += [f"## {h[2]}", ""]
    for e in cv["experience"]:
        out += [f"### {' | '.join(x for x in (e['org'], e['title'], e['dates']) if x)}", ""]
        out += [f"- {b}" for b in e["bullets"]] + [""]
    if cv["projects"]:
        out += [f"## {h[3]}", ""]
        for p in cv["projects"]:
            name = f"[{p['name']}]({p['link']})" if p["link"] else p["name"]
            out += [f"### {name}{' | ' + p['dates'] if p['dates'] else ''}", ""]
            out += [f"- {b}" for b in p["bullets"]] + [""]
    if cv["highlights"]:
        out += [f"## {h[4]}", ""] + [f"- {b}" for b in cv["highlights"]] + [""]
    out += [f"## {h[5]}", ""]
    out += [f"**{e['degree']}** — {e['school']}{' | ' + e['year'] if e['year'] else ''}\n" for e in cv["education"]]
    return "\n".join(out).strip() + "\n"
