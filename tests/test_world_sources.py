import json
from pathlib import Path

import httpx
import pytest

from jd_aggregator import enrich
from jd_aggregator.collectors import boards, linkedin, seek, sites
from jd_aggregator.http import Http
from jd_aggregator.ingest import ingest
from jd_aggregator.lang import detect_lang
from jd_aggregator.models import Posting
from jd_aggregator.normalize import is_web3

FX = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def one_term_one_page(monkeypatch):
    monkeypatch.setattr(seek, "TERMS", ["blockchain"])
    monkeypatch.setattr(linkedin, "TERMS", ["blockchain"])
    monkeypatch.setattr(linkedin, "LOCATIONS", ["Singapore"])
    monkeypatch.setattr(boards, "TERMS", {k: v[:1] for k, v in boards.TERMS.items()})
    monkeypatch.setattr(boards, "PAGES", {k: 1 for k in boards.PAGES})


def _valid(ps, prefix):
    assert ps
    for p in ps:
        assert p.source.startswith(prefix) and p.source_job_id and p.title and p.company and p.url


def test_seek_site(http):
    ps = seek.collect_site(http, "jobsdb-hk")
    _valid(ps, "seek:jobsdb-hk")
    assert all(loc.endswith("Hong Kong") for p in ps for loc in p.locations) and ps[0].posted_at


def test_linkedin_cards_carry_detail_urls(http):
    ps = linkedin.collect(http)
    _valid(ps, "linkedin")
    assert all(p.detail_url.endswith(p.source_job_id) for p in ps) and any(p.posted_at for p in ps)


def test_remote_boards(http):
    for fn, prefix in ((boards.remoteok, "remoteok"), (boards.remotive, "remotive"), (boards.himalayas, "himalayas")):
        _valid(fn(http), prefix)


def test_asian_boards(http):
    w = boards.wanted(http)
    _valid(w, "wanted")
    assert all(p.detail_url for p in w)
    tw = boards.tw104(http)
    _valid(tw, "104")
    assert all("Taiwan" in p.locations[0] for p in tw)


def test_general_boards_keep_only_crypto_jobs(http):
    raw = json.loads((FX / "arbeitnow.json").read_text())["data"]
    ps = boards.arbeitnow(http)
    _valid(ps, "arbeitnow")
    assert 0 < len(ps) == sum(is_web3(f"{j['title']} {j['tags']} {j['description']}") for j in raw) < len(raw)
    assert isinstance(boards.berlinstartupjobs(http), list)


class FakeHttp:
    def __init__(self, pages):
        self.pages, self.calls = pages, []

    def html(self, url):
        self.calls.append(url)
        return self.pages[url]

    page = html


LD = '<script type="application/ld+json">{{"@type":"JobPosting","title":"{}","hiringOrganization":{{"name":"Acme"}},' \
     '"description":"{}"}}</script>'


def test_site_collector_skips_seen_and_rejects_non_crypto(monkeypatch):
    monkeypatch.setitem(sites.SITES, "demo", sites.Site(["https://d.test/list"], r"/job/(\d+)", "https://d.test/job/{}",
                                                        crypto_only=True))
    fake = FakeHttp({"https://d.test/list": '<a href="/job/1"></a><a href="/job/2"></a><a href="/job/3"></a>',
                     "https://d.test/job/2": LD.format("Solidity Engineer", "Build DeFi"),
                     "https://d.test/job/3": LD.format("Barista", "Coffee")})
    ps, rejected = sites.collect(fake, "demo", seen={"1"}, skipped=set())
    assert [(p.source_job_id, p.title) for p in ps] == [("1", ""), ("2", "Solidity Engineer")]
    assert rejected == ["3"] and "https://d.test/job/1" not in fake.calls


def test_html_falls_back_to_browser_when_blocked():
    class FakeBrowser:
        def html(self, url):
            return "<h1>rendered</h1>"

        def close(self):
            pass

    transport = httpx.MockTransport(lambda r: httpx.Response(403, text="<title>Just a moment...</title>"))
    h = Http(min_interval=0, transport=transport, retries=1, browser=FakeBrowser())
    assert h.html("https://blocked.test/job/1") == "<h1>rendered</h1>" and h.browser_fetches == 1


def test_enrich_fills_description_date_and_language(conn):
    ingest(conn, [Posting(source="getro:x", source_job_id="1", company="Circle",
                          title="Director, Partner Management, Americas", url="https://circle.test/job/1")])
    fake = FakeHttp({"https://circle.test/job/1": (FX / "detail_workday.html").read_text()})
    stats = enrich.run(conn, fake, "2026-10-22T00:00:00Z")
    j = conn.execute("SELECT description, posted_at, lang, enrich_status FROM jobs").fetchone()
    assert stats == {"fetched": 1, "new_jobs": 1}
    assert len(j["description"]) > 1000 and j["posted_at"].startswith("2026-10-21") and j["lang"] == "en"
    assert j["enrich_status"] == "ok" and enrich.candidates(conn, "2026-10-22T00:00:00Z", 10) == []


def test_enrich_rejects_a_page_for_another_job(conn):
    ingest(conn, [Posting(source="getro:x", source_job_id="1", company="Acme", title="Rust Engineer",
                          url="https://acme.test/careers")])
    fake = FakeHttp({"https://acme.test/careers": LD.format("Office Manager", "x" * 300)})
    enrich.run(conn, fake, "2026-10-22T00:00:00Z")
    assert conn.execute("SELECT description, enrich_status FROM jobs").fetchone()[:] == (None, "other-page")


def test_detect_lang():
    assert detect_lang("區塊鏈工程師") == "zh" and detect_lang("블록체인 개발자") == "ko"
    assert detect_lang("ブロックチェーンエンジニア") == "ja"
    assert detect_lang("Разработчик", "Ищем опытного разработчика в команду криптобиржи, удалённая работа") == "ru"
