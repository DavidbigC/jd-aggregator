import re

from ..models import Posting
from ..normalize import to_iso
from .base import gather, salary_text

API = "https://api.getro.com/api/v2/collections/{}/search/jobs"
NETWORKS = {
    "blockchain-association": (869, "jobs.theblockchainassociation.org"),
    "dcg": (116, "jobs.dcg.co"),
    "dragonfly": (1118, "jobs.dragonfly.xyz"),
    "polychain": (203, "jobs.polychain.capital"),
    "blockchain-capital": (815, "jobs.blockchaincapital.com"),
    "castle-island": (13362, "jobs.castleisland.vc"),
    "multicoin": (390, "jobs.multicoin.capital"),
    "solana": (858, "jobs.solana.com"),
    "coinbase-ventures": (1625, "coinbase.getro.com"),
    "coinfund": (1032, "jobs.coinfund.io"),
    "variant": (1508, "jobs.variant.fund"),
    "electric": (1640, "jobs.electriccapital.com"),
    "jump-crypto": (20916, "jobs.jumpcrypto.com"),
    "framework": (1127, "jobs.framework.ventures"),
    "arbitrum": (4184, "jobs.arbitrum.io"),
    "delphi": (1440, "jobs.delphiventures.io"),
    "archetype": (2765, "jobs.archetype.fund"),
    "bnb-chain": (3788, "jobs.bnbchain.org"),
    "nascent": (5372, "jobs.nascent.xyz"),
    "spartan": (1179, "jobs.spartangroup.io"),
    "avalanche": (10223, "jobs.avax.network"),
    "placeholder": (922, "jobs.placeholder.vc"),
}


_LINKEDIN_AT = re.compile(r"linkedin\.com/jobs/view/.+-at-([a-z0-9-]+?)-\d+/?$")


# Some networks file LinkedIn-sourced jobs under the wrong portfolio company (e.g. Hadrian jobs as StreamingFast);
# the company slug in the LinkedIn URL is the reliable one.
def _company(org_name: str | None, url: str | None) -> str:
    m = _LINKEDIN_AT.search(url or "")
    if not m:
        return org_name or "Unknown"
    slug = m.group(1).split("-")
    org = {w for w in re.findall(r"[a-z0-9]+", (org_name or "").lower()) if len(w) >= 3}
    return org_name if org_name and org & set(slug) else " ".join(w.capitalize() for w in slug)


def _dollars(cents):
    return cents / 100 if cents else None


def collect_network(http, name: str) -> list[Posting]:
    nid, host = NETWORKS[name]
    headers = {"accept": "application/json", "origin": f"https://{host}", "referer": f"https://{host}/"}
    out, page = [], 0
    while True:
        res = http.post(API.format(nid), json={"hitsPerPage": 20, "page": page, "filters": "", "query": ""},
                        headers=headers).json()["results"]
        for j in res["jobs"]:
            org = j.get("organization") or {}
            page_url = f"https://{host}/companies/{org.get('slug')}/jobs/{j.get('slug')}"
            out.append(Posting(
                source=f"getro:{name}", source_job_id=str(j["id"]), company=_company(org.get("name"), j.get("url")),
                title=j["title"], url=j.get("url") or page_url, detail_url=page_url,
                locations=j.get("locations") or [], remote=(j.get("work_mode") == "remote") or None,
                posted_at=to_iso(j.get("created_at")),
                salary=salary_text(_dollars(j.get("compensation_amount_min_cents")),
                                   _dollars(j.get("compensation_amount_max_cents")), j.get("compensation_currency"),
                                   j.get("compensation_period"))))
        page += 1
        if not res["jobs"] or len(out) >= res["count"]:
            return out


def collect(http) -> list[Posting]:
    return gather(NETWORKS, lambda name: collect_network(http, name))
