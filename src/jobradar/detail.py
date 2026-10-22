import html as htmllib
import json
import re
from dataclasses import dataclass, field

import trafilatura

from .collectors.base import salary_text
from .normalize import html_to_text, to_iso

LD = re.compile(r"<script[^>]*application/ld\+json[^>]*>(.*?)</script>", re.S | re.I)
CONTAINERS = [re.compile(r'class="show-more-less-html__markup[^"]*"[^>]*>(.*?)</div>', re.S)]
H1 = re.compile(r"<h1[^>]*>(.*?)</h1>", re.S | re.I)
OG_TITLE = re.compile(r'<meta[^>]+property="og:title"[^>]+content="([^"]*)"', re.I)


@dataclass
class Detail:
    title: str | None = None
    company: str | None = None
    description: str | None = None
    posted_at: str | None = None
    locations: list[str] = field(default_factory=list)
    salary: str | None = None
    remote: bool | None = None


def parse(page: str) -> Detail:
    if jp := _jobposting(page):
        return _from_ld(jp)
    for rx in CONTAINERS:
        if m := rx.search(page):
            return Detail(title=_title(page), description=html_to_text(m.group(1)))
    return Detail(title=_title(page), description=trafilatura.extract(page, favor_recall=True) or None)


def _jobposting(page: str) -> dict | None:
    for m in LD.finditer(page):
        try:
            data = json.loads(m.group(1).strip(), strict=False)
        except ValueError:
            continue
        stack = [data]
        while stack:
            x = stack.pop()
            if isinstance(x, list):
                stack += x
            elif isinstance(x, dict):
                if "JobPosting" in str(x.get("@type")):
                    return x
                stack += x.get("@graph") or []
    return None


def _name(x) -> str | None:
    if isinstance(x, list):
        x = x[0] if x else None
    if isinstance(x, dict):
        x = x.get("name")
    return htmllib.unescape(str(x)).strip() if x else None


def _place(loc: dict) -> str:
    a = loc.get("address") or {}
    if isinstance(a, str):
        return a
    parts = [a.get("addressLocality"), a.get("addressRegion"), _name(a.get("addressCountry"))]
    parts = [re.sub(r"\s+", " ", str(p).strip().splitlines()[0])[:60] for p in parts if p and str(p).strip()]
    return ", ".join(dict.fromkeys(parts))


def _from_ld(jp: dict) -> Detail:
    locs = jp.get("jobLocation") or []
    locs = [_place(x) for x in (locs if isinstance(locs, list) else [locs]) if isinstance(x, dict)]
    reqs = jp.get("applicantLocationRequirements") or []
    remote = "TELECOMMUTE" in str(jp.get("jobLocationType", "")).upper()
    if remote:
        names = [_name(r) for r in (reqs if isinstance(reqs, list) else [reqs])]
        locs += [f"Remote ({n})" for n in names if n] or ["Remote"]
    pay = jp.get("baseSalary") or {}
    val = pay.get("value") if isinstance(pay, dict) else None
    salary = None
    if isinstance(val, dict):
        salary = salary_text(_num(val.get("minValue") or val.get("value")), _num(val.get("maxValue")),
                             pay.get("currency"), val.get("unitText"))
    return Detail(title=_name(jp.get("title")), company=_name(jp.get("hiringOrganization")),
                  description=html_to_text(jp.get("description")), posted_at=to_iso(jp.get("datePosted")),
                  locations=[x for x in locs if x], salary=salary, remote=remote or None)


def _num(x) -> float | None:
    try:
        return float(x) or None
    except (TypeError, ValueError):
        return None


def _title(page: str) -> str | None:
    m = H1.search(page) or OG_TITLE.search(page)
    return html_to_text(m.group(1)) if m else None
