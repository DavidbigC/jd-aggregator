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
            out.append(Posting(
                source=f"getro:{name}", source_job_id=str(j["id"]), company=org.get("name") or "Unknown",
                title=j["title"], url=j.get("url") or f"https://{host}/companies/{org.get('slug')}/jobs/{j.get('slug')}",
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
