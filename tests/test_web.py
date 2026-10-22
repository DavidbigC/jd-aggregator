import pytest
from fastapi.testclient import TestClient

from jobradar.db import connect
from jobradar.ingest import ingest
from jobradar.models import Posting
from jobradar.normalize import now_iso
from jobradar.web.app import create_app

JD = " ".join(f"latency{i}" for i in range(120))


@pytest.fixture
def client(tmp_path):
    db = tmp_path / "web.db"
    conn = connect(db)
    now = now_iso()
    ingest(conn, [
        Posting(source="ats:ashby:acme", source_job_id="1", company="Acme", title="Rust Engineer",
                locations=["Singapore"], description=JD, from_ats=True, posted_at=now,
                url="https://jobs.ashbyhq.com/acme/0b8f0b8e-1111-2222-3333-444455556666"),
        Posting(source="getro:dragonfly", source_job_id="g1", company="Acme", title="Rust Engineer",
                url="https://jobs.ashbyhq.com/acme/0b8f0b8e-1111-2222-3333-444455556666"),
        Posting(source="cryptojobslist", source_job_id="c1", company="Beta", title="Head of Growth",
                locations=["London"], description="growth marketing lead for a defi wallet", posted_at=now),
        Posting(source="ats:workday:acme", source_job_id="w1", company="Gamma", title="Undated Role"),
        Posting(source="habr", source_job_id="h1", company="Bitbanker", title="Разработчик блокчейн", posted_at=now,
                description="Ищем опытного разработчика в команду криптобиржи, удалённая работа, полный день"),
    ])
    conn.close()
    return TestClient(create_app(db))


def test_jobs_page_lists_deduped_jobs(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.text.count("Rust Engineer") == 1 and "Head of Growth" in r.text
    assert "3 jobs" in r.text.replace("<b>", "").replace("</b>", "")


def test_undated_jobs_only_show_without_a_posted_filter(client):
    assert "Undated Role" not in client.get("/").text
    r = client.get("/", params={"posted": "all"})
    assert "Undated Role" in r.text and "date unknown" in r.text


def test_language_filter_and_tag(client):
    page = client.get("/").text
    assert "Русский" in page and 'class="tag lang"' in page
    r = client.get("/", params=[("lang", "ru")]).text
    assert "Разработчик блокчейн" in r and "Rust Engineer" not in r
    r = client.get("/", params=[("lang", "ru"), ("lang", "en")]).text
    assert "Разработчик блокчейн" in r and "Rust Engineer" in r


def test_filters(client):
    assert "Head of Growth" not in client.get("/", params={"q": "latency5"}).text
    assert "Rust Engineer" not in client.get("/", params={"region": "EMEA"}).text
    assert "Head of Growth" not in client.get("/", params={"source": "ats"}).text
    assert "Rust Engineer" not in client.get("/", params={"source": "board-only"}).text


def test_htmx_requests_get_partials(client):
    r = client.get("/", headers={"HX-Request": "true"})
    assert "<html" not in r.text and "Rust Engineer" in r.text


def test_detail_lists_every_sighting(client):
    r = client.get("/jobs/1", headers={"HX-Request": "true"})
    assert "Seen on 2 sources" in r.text and "getro:dragonfly" in r.text and "ats:ashby:acme" in r.text
    assert client.get("/jobs/999").status_code == 404


def test_companies_and_sources_pages(client):
    assert "Acme" in client.get("/companies").text
    r = client.get("/sources")
    assert r.status_code == 200 and "jobstash" in r.text and "Run now" in r.text
