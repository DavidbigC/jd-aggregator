import defusedxml.ElementTree as ET

from ..models import Posting
from ..normalize import ats_key_from_url, html_to_text, now_iso, relative_posted, to_iso
from .base import salary_text


def _post(ats: str, slug: str, company: str, **kw) -> Posting:
    return Posting(source=f"ats:{ats}:{slug}", company=company, from_ats=True, **kw)


def greenhouse(http, slug, company):
    data = http.get(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs", params={"content": "true"}).json()
    return [
        _post("greenhouse", slug, company, source_job_id=str(j["id"]), title=j["title"], url=j["absolute_url"],
              ats_key=f"gh:{j['id']}", locations=[(j.get("location") or {}).get("name") or ""],
              description=html_to_text(j.get("content")),
              posted_at=to_iso(j.get("first_published") or j.get("updated_at")))
        for j in data["jobs"]
    ]


def lever(http, slug, company, ats="lever"):
    host = "api.eu.lever.co" if ats == "lever-eu" else "api.lever.co"
    out = []
    for j in http.get(f"https://{host}/v0/postings/{slug}", params={"mode": "json"}).json():
        cats = j.get("categories") or {}
        lists = "\n\n".join(f"{x.get('text', '')}\n{html_to_text(x.get('content')) or ''}" for x in j.get("lists") or [])
        intro = j.get("descriptionPlain") or html_to_text(j.get("description"))
        desc = "\n\n".join(x for x in (intro, lists, j.get("additionalPlain")) if x)
        sal = j.get("salaryRange") or {}
        out.append(_post(ats, slug, company, source_job_id=j["id"], title=j["text"], url=j["hostedUrl"],
                         ats_key=f"lever:{j['id']}", locations=cats.get("allLocations") or [cats.get("location") or ""],
                         remote=(j.get("workplaceType") == "remote") or None, description=desc or None,
                         posted_at=to_iso(j.get("createdAt")),
                         salary=salary_text(sal.get("min"), sal.get("max"), sal.get("currency"), sal.get("interval"))))
    return out


def lever_eu(http, slug, company):
    return lever(http, slug, company, ats="lever-eu")


def ashby(http, slug, company):
    data = http.get(f"https://api.ashbyhq.com/posting-api/job-board/{slug}",
                    params={"includeCompensation": "true"}).json()
    out = []
    for j in data["jobs"]:
        if j.get("isListed") is False:
            continue
        comp = j.get("compensation") or {}
        locs = [j.get("location") or ""] + [s.get("location") or "" for s in j.get("secondaryLocations") or []]
        out.append(_post("ashby", slug, company, source_job_id=j["id"], title=j["title"], url=j["jobUrl"],
                         ats_key=ats_key_from_url(j["jobUrl"]) or f"ashby:{j['id']}", locations=locs,
                         remote=j.get("isRemote"), description=j.get("descriptionPlain"),
                         posted_at=to_iso(j.get("publishedAt")),
                         salary=comp.get("scrapeableCompensationSalarySummary") or comp.get("compensationTierSummary")))
    return out


def workable(http, slug, company):
    data = http.get(f"https://apply.workable.com/api/v1/widget/accounts/{slug}", params={"details": "true"}).json()
    out = []
    for j in data["jobs"]:
        locs = [", ".join(x for x in (loc.get("city"), loc.get("country")) if x) for loc in j.get("locations") or []]
        out.append(_post("workable", slug, company, source_job_id=j["shortcode"], title=j["title"], url=j["url"],
                         ats_key=f"workable:{j['shortcode']}", locations=locs, remote=j.get("telecommuting"),
                         description=html_to_text(j.get("description")), posted_at=to_iso(j.get("published_on"))))
    return out


def recruitee(http, slug, company):
    data = http.get(f"https://{slug}.recruitee.com/api/offers/").json()
    return [
        _post("recruitee", slug, company, source_job_id=str(j["id"]), title=j["title"], url=j["careers_url"],
              locations=[x.get("name") or "" for x in j.get("locations") or []] or [j.get("location") or ""],
              remote=j.get("remote"),
              description=html_to_text((j.get("description") or "") + (j.get("requirements") or "")),
              posted_at=to_iso(j.get("published_at")))
        for j in data["offers"]
    ]


def smartrecruiters(http, slug, company):
    data = http.get(f"https://api.smartrecruiters.com/v1/companies/{slug}/postings", params={"limit": 100}).json()
    return [
        _post("smartrecruiters", slug, company, source_job_id=j["id"], title=j["name"],
              url=f"https://jobs.smartrecruiters.com/{slug}/{j['id']}",
              locations=[(j.get("location") or {}).get("fullLocation") or ""],
              remote=(j.get("location") or {}).get("remote"), posted_at=to_iso(j.get("releasedDate")))
        for j in data["content"]
    ]


def bamboohr(http, slug, company):
    out = []
    for j in http.get(f"https://{slug}.bamboohr.com/careers/list").json()["result"]:
        loc = j.get("location") or {}
        out.append(_post("bamboohr", slug, company, source_job_id=str(j["id"]), title=j["jobOpeningName"],
                         url=f"https://{slug}.bamboohr.com/careers/{j['id']}",
                         locations=[", ".join(x for x in (loc.get("city"), loc.get("state")) if x)],
                         remote=bool(j.get("isRemote")) or None))
    return out


def breezy(http, slug, company):
    return [
        _post("breezy", slug, company, source_job_id=j["id"], title=j["name"], url=j["url"],
              locations=[(j.get("location") or {}).get("name") or ""], remote=(j.get("location") or {}).get("is_remote"),
              posted_at=to_iso(j.get("published_date")), salary=j.get("salary") or None)
        for j in http.get(f"https://{slug}.breezy.hr/json").json()
    ]


def teamtailor(http, slug, company):
    root = ET.fromstring(http.get(f"https://{slug}.teamtailor.com/jobs.rss").content)
    return [
        _post("teamtailor", slug, company, source_job_id=it.findtext("guid") or it.findtext("link"),
              title=it.findtext("title"), url=it.findtext("link"),
              description=html_to_text(it.findtext("description")), posted_at=to_iso(it.findtext("pubDate")))
        for it in root.iter("item")
    ]


def personio(http, slug, company):
    root = ET.fromstring(http.get(f"https://{slug}.jobs.personio.de/xml").content)
    out = []
    for pos in root.iter("position"):
        pid = pos.findtext("id")
        desc = "\n\n".join(f"{d.findtext('name') or ''}\n{html_to_text(d.findtext('value')) or ''}"
                           for d in pos.iter("jobDescription"))
        out.append(_post("personio", slug, company, source_job_id=pid, title=pos.findtext("name"),
                         url=f"https://{slug}.jobs.personio.de/job/{pid}",
                         locations=[o.text or "" for o in pos.iter("office")],
                         description=desc or None, posted_at=to_iso(pos.findtext("createdAt"))))
    return out


def rippling(http, slug, company):
    data = http.get(f"https://ats.rippling.com/api/v2/board/{slug}/jobs").json()
    items = data["items"] if isinstance(data, dict) else data
    return [
        _post("rippling", slug, company, source_job_id=j["id"], title=j["name"].strip(), url=j["url"],
              locations=[x.get("name") or "" for x in j.get("locations") or []],
              remote=any(x.get("workplaceType") == "REMOTE" for x in j.get("locations") or []) or None)
        for j in items
    ]


def gem(http, slug, company):
    return [
        _post("gem", slug, company, source_job_id=str(j.get("id") or j["absolute_url"].rsplit("/", 1)[-1]),
              title=j["title"], url=j["absolute_url"], locations=[(j.get("location") or {}).get("name") or ""],
              description=j.get("content_plain") or html_to_text(j.get("content")),
              posted_at=to_iso(j.get("first_published_at") or j.get("updated_at")))
        for j in http.get(f"https://api.gem.com/job_board/v0/{slug}/job_posts/").json()
    ]


def workday(http, slug, company):
    tenant, wd, site = slug.split("|")
    base = f"https://{tenant}.{wd}.myworkdayjobs.com"
    out, offset, total, now = [], 0, None, now_iso()
    while total is None or offset < total:
        data = http.post(f"{base}/wday/cxs/{tenant}/{site}/jobs",
                         json={"appliedFacets": {}, "limit": 20, "offset": offset, "searchText": ""}).json()
        total = data.get("total") if total is None else total
        posts = data.get("jobPostings") or []
        if not posts:
            break
        for j in posts:
            out.append(_post("workday", slug, company, source_job_id=j["externalPath"], title=j["title"],
                             url=f"{base}/en-US/{site}{j['externalPath']}", locations=[j.get("locationsText") or ""],
                             posted_at=relative_posted(j.get("postedOn"), now)))
        offset += len(posts)
    return out


ADAPTERS = {
    "greenhouse": greenhouse, "lever": lever, "lever-eu": lever_eu, "ashby": ashby, "workable": workable,
    "recruitee": recruitee, "smartrecruiters": smartrecruiters, "bamboohr": bamboohr, "breezy": breezy,
    "teamtailor": teamtailor, "personio": personio, "rippling": rippling, "gem": gem, "workday": workday,
}
