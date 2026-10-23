from ..models import Posting
from ..normalize import ats_key_from_url, to_iso
from .base import salary_text

URL = "https://middleware.jobstash.xyz/jobs/list"


def _text(v) -> str:
    if isinstance(v, list):
        return "\n".join(f"• {x}" for x in v if x)
    return v or ""


def collect(http) -> list[Posting]:
    out, page = [], 1
    while True:
        data = http.get(URL, params={"page": page, "limit": 1000}).json()
        for j in data["data"]:
            org = j.get("organization") or {}
            if not (org.get("isCrypto") or org.get("vertical") == "crypto") or not j.get("title"):
                continue
            parts = (j.get("summary"), j.get("description"), j.get("responsibilities"), j.get("requirements"))
            desc = "\n\n".join(t for t in map(_text, parts) if t)
            out.append(Posting(
                source="jobstash", source_job_id=j["shortUUID"], company=org.get("name") or "Unknown",
                title=j["title"], url=j.get("url") or f"https://jobstash.xyz/jobs/{j['shortUUID']}",
                ats_key=ats_key_from_url(j.get("url")),
                locations=[j["location"]] if j.get("location") else [],
                remote=(j.get("locationType") == "REMOTE") or None, description=desc or None,
                posted_at=to_iso(j.get("timestamp")), company_website=org.get("website"),
                salary=salary_text(j.get("minimumSalary"), j.get("maximumSalary"), j.get("salaryCurrency"))))
        if len(data["data"]) < 1000 or page * 1000 >= data["total"]:
            return out
        page += 1
