import re

from ..models import Posting
from ..normalize import to_iso

URL = "https://api.github.com/repos/rebase-network/who-is-hiring/issues"


def collect(http) -> list[Posting]:
    issues = http.get(URL, params={"state": "open", "per_page": 100},
                      headers={"Accept": "application/vnd.github+json"}).json()
    out = []
    for i in issues:
        if "pull_request" in i:
            continue
        m = re.match(r"\s*[\[【]([^\]】]+)[\]】]\s*(.*)", i["title"])
        locs = [s.strip() for s in re.split(r"[/、,，]", m.group(1)) if s.strip()] if m else []
        title = (m.group(2) if m else i["title"]).strip() or i["title"]
        out.append(Posting(source="rebase", source_job_id=str(i["number"]), company="未具名 (Rebase)", title=title,
                           url=i["html_url"], locations=locs, description=i.get("body"),
                           posted_at=to_iso(i.get("created_at"))))
    return out
