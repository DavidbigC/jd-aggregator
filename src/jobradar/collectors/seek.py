from ..models import Posting
from ..normalize import to_iso
from .base import gather

SITES = {
    "jobsdb-hk": ("hk.jobsdb.com", "HK-Main", "Hong Kong"),
    "jobsdb-th": ("th.jobsdb.com", "TH-Main", "Thailand"),
    "jobstreet-sg": ("sg.jobstreet.com", "SG-Main", "Singapore"),
    "jobstreet-my": ("my.jobstreet.com", "MY-Main", "Malaysia"),
    "jobstreet-ph": ("ph.jobstreet.com", "PH-Main", "Philippines"),
    "jobstreet-id": ("id.jobstreet.com", "ID-Main", "Indonesia"),
}
TERMS = ["blockchain", "crypto", "web3"]
PAGES = 1


def collect_site(http, key: str) -> list[Posting]:
    host, site_key, country = SITES[key]
    out = []
    for term in TERMS:
        for page in range(1, PAGES + 1):
            data = http.get(f"https://{host}/api/jobsearch/v5/search",
                            params={"siteKey": site_key, "keywords": term, "page": page, "pageSize": 100}).json()
            for j in data.get("data") or []:
                bullets = [f"• {b}" for b in j.get("bulletPoints") or []]
                locs = [x.get("label") for x in j.get("locations") or [] if x.get("label")]
                out.append(Posting(
                    source=f"seek:{key}", source_job_id=str(j["id"]),
                    company=j.get("companyName") or (j.get("advertiser") or {}).get("description") or "Unknown",
                    title=j["title"], url=f"https://{host}/job/{j['id']}", locations=[f"{x}, {country}" for x in locs]
                    or [country], remote="remote" in str(j.get("workArrangements")).lower() or None,
                    description="\n".join(filter(None, [j.get("teaser"), *bullets])) or None,
                    posted_at=to_iso(j.get("listingDate")), salary=j.get("salaryLabel") or None))
            if page * 100 >= (data.get("totalCount") or 0):
                break
    return out


def collect(http) -> list[Posting]:
    return gather(SITES, lambda key: collect_site(http, key))
