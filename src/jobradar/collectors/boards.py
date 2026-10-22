import html
import re

import defusedxml.ElementTree as ET

from ..models import Posting
from ..normalize import html_to_text, is_web3, to_iso
from .base import gather, salary_text

TERMS = {
    "remoteok": ["crypto", "web3", "blockchain"],
    "remotive": ["crypto", "blockchain", "web3"],
    "himalayas": ["crypto", "web3", "blockchain"],
    "wanted": ["블록체인", "가상자산", "web3", "크립토"],
    "104": ["區塊鏈", "加密貨幣", "web3"],
}
PAGES = {"himalayas": 5, "104": 5, "arbeitnow": 5}


def _relevant(*parts) -> bool:
    return is_web3(" ".join(str(p) for p in parts if p))


def remoteok(http) -> list[Posting]:
    def tag(t):
        rows = [j for j in http.get("https://remoteok.com/api", params={"tag": t}).json() if "id" in j]
        return [Posting(source="remoteok", source_job_id=str(j["id"]), company=j["company"], title=j["position"],
                        url=j.get("url"), locations=[j["location"]] if j.get("location") else ["Remote"], remote=True,
                        description=html_to_text(j.get("description")), posted_at=to_iso(j.get("date")),
                        salary=salary_text(j.get("salary_min"), j.get("salary_max"), "USD", "year"))
                for j in rows]
    return gather(TERMS["remoteok"], tag)


def remotive(http) -> list[Posting]:
    def search(t):
        jobs = http.get("https://remotive.com/api/remote-jobs", params={"search": t}).json()["jobs"]
        return [Posting(source="remotive", source_job_id=str(j["id"]), company=j["company_name"], title=j["title"],
                        url=j["url"], locations=[j.get("candidate_required_location") or "Remote"], remote=True,
                        description=html_to_text(j.get("description")), posted_at=to_iso(j.get("publication_date")),
                        salary=j.get("salary") or None)
                for j in jobs if _relevant(j["title"], j.get("description"), j.get("tags"))]
    return gather(TERMS["remotive"], search)


def himalayas(http) -> list[Posting]:
    def search(t):
        out = []
        for page in range(1, PAGES["himalayas"] + 1):
            jobs = http.get("https://himalayas.app/jobs/api/search", params={"q": t, "page": page}).json()["jobs"]
            out += [Posting(source="himalayas", source_job_id=j["guid"], company=j["companyName"], title=j["title"],
                            url=j.get("applicationLink") or j["guid"], remote=True,
                            locations=[f"Remote ({x})" for x in j.get("locationRestrictions") or []] or ["Remote"],
                            description=html_to_text(j.get("description")), posted_at=to_iso(j.get("pubDate")),
                            salary=salary_text(j.get("minSalary"), j.get("maxSalary"), j.get("currency"),
                                               j.get("salaryPeriod")))
                    for j in jobs]
            if len(jobs) < 20:
                break
        return out
    return gather(TERMS["himalayas"], search)


def wanted(http) -> list[Posting]:
    def search(t):
        data = http.get("https://www.wanted.co.kr/api/chaos/search/v1/results",
                        params={"query": t, "limit": 100}).json()["positions"]["data"]
        return [Posting(source="wanted", source_job_id=str(j["id"]), company=j["company"]["name"],
                        title=j["position"], url=f"https://www.wanted.co.kr/wd/{j['id']}",
                        locations=[", ".join(filter(None, [(j.get("address") or {}).get("location"), "Korea"]))],
                        detail_url=f"https://www.wanted.co.kr/wd/{j['id']}")
                for j in data]
    return gather(TERMS["wanted"], search)


def tw104(http) -> list[Posting]:
    def search(t):
        out = []
        for page in range(1, PAGES["104"] + 1):
            data = http.get("https://www.104.com.tw/jobs/search/api/jobs",
                            params={"keyword": t, "page": page, "pagesize": 20},
                            headers={"Referer": "https://www.104.com.tw/jobs/search/"}).json()
            for j in data["data"]:
                if not _relevant(j["jobName"], j.get("description")):
                    continue
                lo, hi = int(j.get("salaryLow") or 0), int(j.get("salaryHigh") or 0)
                out.append(Posting(source="104", source_job_id=str(j["jobNo"]), company=j["custName"],
                                   title=j["jobName"], url=j["link"]["job"],
                                   locations=[f"{j.get('jobAddrNoDesc') or ''}, Taiwan".lstrip(", ")],
                                   description=j.get("description"), posted_at=to_iso(_ymd(j.get("appearDate"))),
                                   salary=salary_text(lo, hi if hi < 9999999 else None, "TWD", "month")))
            if page >= (data.get("metadata", {}).get("pagination", {}).get("lastPage") or 0):
                break
        return out
    return gather(TERMS["104"], search)


def _ymd(s: str | None) -> str | None:
    return f"{s[:4]}-{s[4:6]}-{s[6:8]}" if s and len(s) == 8 else None


def arbeitnow(http) -> list[Posting]:
    out = []
    for page in range(1, PAGES["arbeitnow"] + 1):
        for j in http.get("https://www.arbeitnow.com/api/job-board-api", params={"page": page}).json()["data"]:
            if _relevant(j["title"], j.get("tags"), j.get("description")):
                out.append(Posting(source="arbeitnow", source_job_id=j["slug"], company=j["company_name"],
                                   title=j["title"], url=j["url"], locations=[j.get("location") or ""],
                                   remote=j.get("remote"), description=html_to_text(j.get("description")),
                                   posted_at=to_iso(j.get("created_at"))))
    return out


def berlinstartupjobs(http) -> list[Posting]:
    root = ET.fromstring(http.get("https://berlinstartupjobs.com/feed/").content)
    out = []
    for it in root.iter("item"):
        title, desc = html.unescape(it.findtext("title") or ""), it.findtext("description") or ""
        if not _relevant(title, desc):
            continue
        role, _, company = title.rpartition(" // ")
        out.append(Posting(source="berlinstartupjobs", source_job_id=it.findtext("guid") or it.findtext("link"),
                           company=company or "Unknown", title=role or title, url=it.findtext("link"),
                           locations=["Berlin, Germany"], description=html_to_text(re.sub(r"<img[^>]*>", "", desc)),
                           posted_at=to_iso(it.findtext("pubDate"))))
    return out
