import html
import re

import defusedxml.ElementTree as ET

from ..models import Posting
from ..normalize import html_to_text, to_iso

DC = "{http://purl.org/dc/elements/1.1/}"
WEB3_WORDS = re.compile(r"web3|crypto|blockchain|defi|solidity|nft|区块链|加密货币|数字货币|币圈|链上|交易所|量化|钱包", re.I)


def _items(http, url: str):
    return list(ET.fromstring(http.get(url).content).iter("item"))


def _slug(url: str) -> str:
    return url.split("?")[0].rstrip("/").rsplit("/", 1)[-1]


def _role_at_company(title: str | None) -> tuple[str, str]:
    role, sep, company = html.unescape(title or "").rpartition(" at ")
    return (role.strip(), company.strip()) if sep and role.strip() else ((title or "").strip(), "Unknown")


def cryptojobslist(http) -> list[Posting]:
    return [
        Posting(source="cryptojobslist", source_job_id=_slug(it.findtext("link")),
                company=html.unescape(it.findtext(f"{DC}creator") or "Unknown"),
                title=html.unescape(it.findtext("title")).strip(),
                url=it.findtext("link"), description=html_to_text(it.findtext("description")))
        for it in _items(http, "https://api.cryptojobslist.com/jobs.rss")
    ]


def _role_feed(http, source: str, url: str) -> list[Posting]:
    out = []
    for it in _items(http, url):
        role, company = _role_at_company(it.findtext("title"))
        link = it.findtext("guid") or it.findtext("link")
        desc = it.findtext("description") or ""
        loc = re.search(r"Location:\s*</strong>\s*([^<]+)", desc)
        out.append(Posting(source=source, source_job_id=_slug(link), company=company, title=role, url=link,
                           locations=[loc.group(1).strip()] if loc else [], description=html_to_text(desc),
                           posted_at=to_iso(it.findtext("pubDate"))))
    return out


def cryptocurrencyjobs(http) -> list[Posting]:
    return _role_feed(http, "cryptocurrencyjobs", "https://cryptocurrencyjobs.co/index.xml")


def web3vacancy(http) -> list[Posting]:
    return _role_feed(http, "web3vacancy", "https://web3vacancy.com/feed.xml")


def cryptojobs(http) -> list[Posting]:
    return _role_feed(http, "cryptojobs", "https://crypto.jobs/feed/rss")


def eleduck(http) -> list[Posting]:
    out = []
    for it in _items(http, "https://eleduck.com/feed/latest.xml"):
        title, desc = (it.findtext("title") or "").strip(), it.findtext("description") or ""
        if WEB3_WORDS.search(f"{title} {desc}"):
            out.append(Posting(source="eleduck", source_job_id=_slug(it.findtext("link")), company="未具名 (电鸭)",
                               title=title, url=it.findtext("link"), description=html_to_text(desc),
                               posted_at=to_iso(it.findtext("pubDate"))))
    return out
