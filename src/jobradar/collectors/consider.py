import re

from ..models import Posting
from ..normalize import to_iso
from .base import gather, salary_text

BOARDS = {"pantera": "jobs.panteracapital.com", "hashed": "jobs.hashed.com", "bain-crypto": "jobs.baincapitalcrypto.com"}


def _value(v):
    return v.get("value") if isinstance(v, dict) else v


def collect_board(http, name: str) -> list[Posting]:
    host = BOARDS[name]
    page = http.get(f"https://{host}/jobs").text
    token = re.search(r'"csrfToken":"([^"]+)"', page).group(1)
    board_id = re.search(r'"board":\{"id":"([^"]+)"', page).group(1)
    headers = {"x-csrf-token": token, "referer": f"https://{host}/jobs", "origin": f"https://{host}"}
    out, seq = [], None
    while True:
        meta = {"size": 100, **({"sequence": seq} if seq else {})}
        data = http.post(f"https://{host}/api-boards/search-jobs", headers=headers,
                         json={"meta": meta, "board": {"id": board_id, "isParent": True},
                               "query": {"promoteFeatured": False}}).json()
        for j in data["jobs"]:
            sal = j.get("salary") or {}
            out.append(Posting(
                source=f"consider:{name}", source_job_id=j["jobId"], company=j.get("companyName") or "Unknown",
                title=j["title"], url=j.get("url") or j.get("applyUrl"), locations=j.get("locations") or [],
                remote=j.get("remote"), posted_at=to_iso(j.get("timeStamp")),
                salary=salary_text(sal.get("minValue"), sal.get("maxValue"), _value(sal.get("currency")),
                                   _value(sal.get("period")))))
        seq = (data.get("meta") or {}).get("sequence")
        if not data["jobs"] or not seq or len(out) >= data.get("total", 0):
            return out


def collect(http) -> list[Posting]:
    return gather(BOARDS, lambda name: collect_board(http, name))
