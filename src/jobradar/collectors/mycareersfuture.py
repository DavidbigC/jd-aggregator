from ..models import Posting
from ..normalize import html_to_text, to_iso
from .base import gather, salary_text

URL = "https://api.mycareersfuture.gov.sg/v2/jobs"
TERMS = ["blockchain", "crypto", "web3", "digital assets"]


def collect_term(http, term: str) -> list[Posting]:
    out = []
    for j in http.get(URL, params={"search": term, "limit": 100, "page": 0}).json()["results"]:
        sal, md = j.get("salary") or {}, j.get("metadata") or {}
        out.append(Posting(
            source="mycareersfuture", source_job_id=j["uuid"],
            company=(j.get("postedCompany") or {}).get("name") or "Unknown", title=j["title"],
            url=md.get("jobDetailsUrl"), locations=["Singapore"], description=html_to_text(j.get("description")),
            posted_at=to_iso(md.get("newPostingDate")),
            salary=salary_text(sal.get("minimum"), sal.get("maximum"), "SGD",
                               (sal.get("type") or {}).get("salaryType"))))
    return out


def collect(http) -> list[Posting]:
    return gather(TERMS, lambda t: collect_term(http, t))
