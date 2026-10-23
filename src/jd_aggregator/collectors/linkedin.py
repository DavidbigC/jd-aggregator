import html
import re

from ..models import Posting
from ..normalize import to_iso
from .base import gather

SEARCH = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
TERMS = ["blockchain", "crypto", "web3"]
LOCATIONS = ["Worldwide", "Singapore", "Hong Kong SAR", "United Arab Emirates", "United Kingdom", "United States"]
CARD = re.compile(r'data-entity-urn="urn:li:jobPosting:(\d+)"(.*?)(?=data-entity-urn="urn:li:jobPosting:|\Z)', re.S)


def _field(card: str, cls: str) -> str | None:
    m = re.search(rf'class="[^"]*{cls}[^"]*"[^>]*>(.*?)</', card, re.S)
    return html.unescape(re.sub(r"<[^>]+>|\s+", " ", m.group(1))).strip() if m else None


def parse(page: str) -> list[Posting]:
    out = []
    for job_id, card in CARD.findall(page):
        title, company = _field(card, "base-search-card__title"), _field(card, "base-search-card__subtitle")
        if not title or not company:
            continue
        when = re.search(r'datetime="([^"]+)"', card)
        loc = _field(card, "job-search-card__location")
        out.append(Posting(source="linkedin", source_job_id=job_id, company=company, title=title,
                           url=f"https://www.linkedin.com/jobs/view/{job_id}", locations=[loc] if loc else [],
                           posted_at=to_iso(when.group(1)) if when else None,
                           detail_url=f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"))
    return out


def collect(http) -> list[Posting]:
    pairs = [(t, loc) for t in TERMS for loc in LOCATIONS]
    return gather(pairs, lambda p: parse(http.get(SEARCH, params={"keywords": p[0], "location": p[1],
                                                                   "f_TPR": "r604800", "start": 0}).text))
