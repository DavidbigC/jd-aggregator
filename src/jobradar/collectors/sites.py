import re
from dataclasses import dataclass, field
from urllib.parse import quote

from .. import detail
from ..models import Posting
from ..normalize import is_web3

MAX_NEW = 60


@dataclass
class Site:
    lists: list[str]
    link: str
    detail: str
    browser: bool = False
    crypto_only: bool = False
    company: str | None = None
    company_from_id: str | None = None
    title_re: str | None = None
    terms: list[str] = field(default_factory=list)


def _q(*terms: str) -> list[str]:
    return [quote(t) for t in terms]


SITES = {
    "habr": Site(["https://career.habr.com/vacancies?q={}&type=all"], r"/vacancies/(\d{7,})",
                 "https://career.habr.com/vacancies/{}", crypto_only=True, terms=_q("blockchain", "crypto", "web3")),
    "hh": Site(["https://hh.ru/search/vacancy?text={}&items_on_page=100"], r"hh\.ru/vacancy/(\d+)",
               "https://hh.ru/vacancy/{}", crypto_only=True, terms=_q("blockchain", "криптовалюта", "web3")),
    "dou": Site(["https://jobs.dou.ua/vacancies/?search={}"], r"jobs\.dou\.ua/companies/([\w.-]+/vacancies/\d+)",
                "https://jobs.dou.ua/companies/{}/", browser=True, crypto_only=True,
                company_from_id=r"^([\w.-]+)/", terms=_q("blockchain", "crypto", "web3")),
    "justjoin": Site(["https://justjoin.it/job-offers/all-locations?keyword={}"], r"/job-offer/([a-z0-9-]+)",
                     "https://justjoin.it/job-offer/{}", crypto_only=True, terms=_q("blockchain", "crypto", "web3")),
    "nofluff": Site(["https://nofluffjobs.com/pl/blockchain"], r"/pl/job/([a-z0-9-]+)",
                    "https://nofluffjobs.com/pl/job/{}", crypto_only=True),
    "green": Site(["https://www.green-japan.com/search?keyword={}"], r"/company/(\d+/job/\d+)",
                  "https://www.green-japan.com/company/{}", crypto_only=True,
                  terms=_q("ブロックチェーン", "暗号資産", "web3")),
    "rocketpunch": Site(["https://www.rocketpunch.com/en/jobs?keywords={}"], r"/jobs/(\d+)",
                        "https://www.rocketpunch.com/en/jobs/{}", crypto_only=True,
                        terms=_q("blockchain", "web3", "블록체인")),
    "cutshort": Site(["https://cutshort.io/jobs/blockchain-jobs", "https://cutshort.io/jobs/web3-jobs"],
                     r"/job/([A-Za-z0-9-]{8,})(?=[\"?])", "https://cutshort.io/job/{}", crypto_only=True),
    "itviec": Site(["https://itviec.com/it-jobs/blockchain"], r"/it-jobs/([a-z0-9-]+-\d{3,})",
                   "https://itviec.com/it-jobs/{}", crypto_only=True),
    "remote3": Site(["https://www.remote3.co/"], r"/remote-jobs/([a-z0-9-]+)", "https://www.remote3.co/remote-jobs/{}",
                    browser=True, title_re=r"^(?:Job Application for )?(.+?)(?: at [^@]+)?$"),
    "djinni": Site(["https://djinni.co/jobs/rss/?primary_keyword=Blockchain",
                    "https://djinni.co/jobs/rss/?keywords=crypto"], r"djinni\.co/jobs/(\d+-[a-z0-9-]+)/", "https://djinni.co/jobs/{}/", crypto_only=True),
    "foresight": Site(["https://foresightnews.pro/job"], r"/job/detail/(\d+)", "https://foresightnews.pro/job/detail/{}",
                      company="未具名 (Foresight)"),
    "learnblockchain": Site(["https://learnblockchain.cn/jobs"], r"/job/(\d+)", "https://learnblockchain.cn/job/{}",
                            company="未具名 (登链社区)"),
    "bitflyer": Site(["https://about.bitflyer.com/en/recruit", "https://about.bitflyer.com/ja/recruit"],
                     r"recruit\.jobcan\.jp/bitflyer/job_offers/(\d+)", "https://recruit.jobcan.jp/bitflyer/job_offers/{}",
                     company="bitFlyer"),
}


def _get(http, site: Site, url: str) -> str:
    return http.page(url) if site.browser else http.html(url)


def collect(http, name: str, seen: set[str], skipped: set[str]) -> tuple[list[Posting], list[str]]:
    site = SITES[name]
    lists = [u.format(t) for u in site.lists for t in (site.terms or [""])]
    ids, errors = [], []
    for url in lists:
        try:
            ids += re.findall(site.link, _get(http, site, url))
        except Exception as e:
            errors.append(f"{url}: {e!r}")
    if errors and not ids:
        raise RuntimeError("; ".join(errors)[:1000])
    ids = list(dict.fromkeys(ids))
    out = [Posting(source=name, source_job_id=i, company="", title="", url=site.detail.format(i))
           for i in ids if i in seen]
    rejected = []
    for i in [i for i in ids if i not in seen and i not in skipped][:MAX_NEW]:
        url = site.detail.format(i)
        try:
            d = detail.parse(_get(http, site, url))
        except Exception:
            continue
        if not d.title:
            continue
        if site.crypto_only and not is_web3(f"{d.title} {d.description or ''}"):
            rejected.append(i)
            continue
        if site.title_re and (m := re.match(site.title_re, d.title)):
            d.title = m.group(1)
        company = d.company or site.company
        if not company and site.company_from_id and (m := re.search(site.company_from_id, i)):
            company = m.group(1)
        out.append(Posting(source=name, source_job_id=i, company=company or "Unknown", title=d.title, url=url,
                           locations=d.locations, remote=d.remote, description=d.description,
                           posted_at=d.posted_at, salary=d.salary))
    return out, rejected
