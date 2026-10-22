import json
import re

from ..config import STALE_DAYS
from ..normalize import ago_iso

MIN_AD = 500
KEEP = re.compile(r"analy|product|growth|insight|research|strateg|data|business intelligence|\bbi\b|reporting|"
                  r"on-?chain|defi|tokenomic|economist|market structure|trading op|ecosystem|"
                  r"产品|分析|数据|研究|策略", re.I)
BACKEND = re.compile(r"back-?end|python|data engineer|platform|api\b|integration|后端", re.I)
DROP = re.compile(r"legal|counsel|accountant|accounting|payroll|recruit|talent|designer|support|security|frontend|"
                  r"front-end|mobile|\bios\b|android|solidity|smart contract|c\+\+|intern|实习|"
                  r"accelerator program|\bBAP\b|filmmaker|\bsoc\b|\bnoc\b|network engineer|site reliability|"
                  r"people business partner|identity access|creative|credit analyst|billing analyst|livechat|"
                  r"client service|portfolio manager|finance system|machine learning|\bml\b|pre-?training|"
                  r"post-?training|reinforcement learning|\brl\b|inference|robotics|chip design", re.I)
ANALYST = re.compile(r"analy|data|insight|business intelligence|\bbi\b|分析|数据", re.I)
# Engineering titles a backend "no" removes; analytics engineers stay.
ENGINEER = re.compile(r"engineer|developer|architect|technical staff|工程[师師]|开发|開發", re.I)
# Analyst work types a "no" (or, for compliance, anything but yes/maybe) removes by title.
ANALYST_TYPES = {
    "risk_fraud": re.compile(r"risk|fraud|风控", re.I),
    "compliance_kyc_aml": re.compile(r"complian|\bkyc\b|\baml\b|financial crime|sanction|合规", re.I),
    "trading_market_ops": re.compile(r"trading|market op", re.I),
    "bi_reporting": re.compile(r"business intelligence|\bbi\b|reporting", re.I),
    "onchain_analytics": re.compile(r"on-?chain|链上", re.I),
    "token_market_research": re.compile(r"tokenomic|market research|token", re.I),
}
# Other job families a "no" removes, unless the title also says analyst / data.
TRACKS = {
    "product": re.compile(r"product|产品", re.I),
    "research": re.compile(r"research|economist|研究", re.I),
    "ops_strategy": re.compile(r"strateg|operations|\bops\b|策略|运营", re.I),
    "growth": re.compile(r"growth|marketing|marketer|business development|增长", re.I),
    "quant": re.compile(r"quant|量化", re.I),
}
REGIONS = {
    "uk": {"GB", "GI"},
    "europe": {"DE", "FR", "NL", "IE", "PT", "ES", "IT", "PL", "CZ", "AT", "HU", "RO", "BG", "GR", "CY", "MT", "LU",
               "BE", "SE", "DK", "NO", "FI", "EE", "LT", "LV", "CH", "IS", "UA", "RS"},
    "us": {"US"},
    "americas": {"CA", "MX", "BR", "AR", "CO", "CL", "PE", "UY", "BM", "KY", "BS"},
    "apac": {"SG", "JP", "KR", "IN", "VN", "TH", "ID", "MY", "PH", "AU", "NZ", "PK"},
    "greater_china": {"CN", "HK", "TW"},
    "middle_east": {"AE", "IL", "SA", "QA", "BH", "EG", "TR"},
}
REGION_WORDS = [
    (re.compile(r"emea|europe|\beu\b|european", re.I), {"uk", "europe"}),
    (re.compile(r"apac|asia", re.I), {"apac", "greater_china"}),
    (re.compile(r"americas|latam|north america", re.I), {"us", "americas"}),
    (re.compile(r"mena|middle east", re.I), {"middle_east"}),
]
DEFAULT_REGIONS = {"uk", "europe"}


def regions_of(countries: list[str], locations: list[str]) -> set[str]:
    out = {name for name, codes in REGIONS.items() if codes & set(countries)}
    if len(out) < len(countries):
        out.add("other")
    text = " | ".join(locations)
    for rx, names in REGION_WORDS:
        if rx.search(text):
            out |= names
    return out


def place(job: dict, prefs: dict) -> str | None:
    locs, countries = job["locations"], job["countries"]
    if job["remote"]:
        if job["remote_scope"] == "anywhere" or sum(loc.startswith("Remote (") for loc in locs) >= 5:
            return "remote anywhere"
        if any(loc.strip().lower() == "remote" for loc in locs):
            return "remote"
        regions = regions_of(countries, locs)
        if not regions:
            return "remote"
        if len(countries) == 1 and prefs.get("single_country_remote") == "hide":
            return None
        if (len(countries) == 1 and prefs.get("single_country_remote") == "uk_eu_only"
                and not regions & {"uk", "europe"}):
            return None
        allowed = set(prefs.get("remote_regions") or DEFAULT_REGIONS)
        return "remote, limited to a region" if regions & allowed else None
    if prefs.get("location") == "remote_or_uk_office" and "GB" in countries:
        return "UK office"
    return None


def title_fits(job: dict, prefs: dict) -> bool:
    title = job["title"]
    analyst, others = prefs.get("analyst_types") or {}, prefs.get("other_tracks") or {}
    if DROP.search(title) or job["seniority"] in ("intern", "exec"):
        return False
    for name, rx in ANALYST_TYPES.items():
        level = analyst.get(name)
        if rx.search(title) and (level == "no" or (name == "compliance_kyc_aml" and level not in ("yes", "maybe"))):
            return False
    for name, rx in TRACKS.items():
        if others.get(name) == "no" and rx.search(title) and not ANALYST.search(title):
            return False
    if others.get("backend") == "no" and ENGINEER.search(title) and not re.search(r"analy|分析", title, re.I):
        return False
    if KEEP.search(title) or job["role"] in ("product", "data", "research"):
        return True
    if analyst.get("compliance_kyc_aml") in ("yes", "maybe") and ANALYST_TYPES["compliance_kyc_aml"].search(title):
        return True
    return job["role"] == "engineering" and bool(BACKEND.search(title)) and others.get("backend") != "no"


def run(conn, prefs: dict, now: str) -> tuple[list[dict], list[tuple[str, int]]]:
    """Free, rule-based cut of the active crypto pool. Returns the kept jobs and the count after each step."""
    rows = conn.execute(
        "SELECT j.id, j.title, j.title_key, j.company_id, c.name AS company, j.locations, j.countries, j.remote, "
        "j.remote_scope, j.role, j.seniority, j.lang, j.salary, j.posted_at, j.first_seen_at, j.description, "
        "j.apply_url FROM jobs j JOIN companies c ON c.id = j.company_id "
        "WHERE c.sector = 'crypto' AND j.last_seen_at >= ?", (ago_iso(now, days=STALE_DAYS),)).fetchall()
    jobs = [{**dict(r), "locations": json.loads(r["locations"]), "countries": json.loads(r["countries"])}
            for r in rows]
    steps = [("Active crypto jobs", len(jobs))]
    since = ago_iso(now, days=prefs.get("fresh_days") or 14)
    jobs = [j for j in jobs if (j["posted_at"] or j["first_seen_at"]) >= since]
    steps.append((f"Posted in the last {prefs.get('fresh_days') or 14} days", len(jobs)))
    jobs = [j for j in jobs if title_fits(j, prefs)]
    steps.append(("Title fits your job families", len(jobs)))
    for j in jobs:
        j["place"] = place(j, prefs)
    jobs = [j for j in jobs if j["place"]]
    steps.append(("Location fits", len(jobs)))
    langs = set(prefs.get("ad_languages") or ["en", "zh"])
    jobs = [j for j in jobs if j["lang"] in langs or j["lang"] is None]
    steps.append(("Ad language fits", len(jobs)))
    newest: dict[tuple, dict] = {}
    for j in sorted(jobs, key=lambda j: j["posted_at"] or j["first_seen_at"]):
        newest[(j["company_id"], j["title_key"])] = j
    jobs = sorted(newest.values(), key=lambda j: j["id"])
    steps.append(("One per company and title", len(jobs)))
    return jobs, steps
