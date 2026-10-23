import pytest
from fastapi.testclient import TestClient

from jobradar.classify import company_sectors
from jobradar.db import connect
from jobradar.ingest import ingest
from jobradar.models import Posting
from jobradar.normalize import now_iso
from jobradar.web.app import create_app

JD = "blockchain " + " ".join(f"latency{i}" for i in range(120))


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
        Posting(source="linkedin", source_job_id="l1", company="Delta Bank", title="Senior Data Analyst",
                locations=["Remote - USA"], remote=True, salary="USD 100k", posted_at=now),
        Posting(source="habr", source_job_id="h1", company="Bitbanker", title="Разработчик блокчейн", posted_at=now,
                description="Ищем опытного разработчика в команду криптобиржи, удалённая работа, полный день"),
    ])
    company_sectors(conn)
    conn.close()
    return TestClient(create_app(db, sectors_csv=tmp_path / "company_sectors.csv"))


def test_jobs_page_lists_deduped_jobs(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.text.count("Rust Engineer") == 1 and "Head of Growth" in r.text
    assert "3 jobs" in r.text.replace("<b>", "").replace("</b>", "")


def test_undated_jobs_only_show_without_a_posted_filter(client):
    assert "Undated Role" not in client.get("/").text
    r = client.get("/", params={"posted": "all", "sector": "all"})
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


def test_crypto_companies_by_default(client):
    assert "Senior Data Analyst" not in client.get("/").text
    assert "Senior Data Analyst" in client.get("/", params={"sector": "all"}).text


def test_role_seniority_country_remote_salary_exclude(client):
    def titles(**params):
        text = client.get("/", params={"sector": "all", **params}).text
        return {t for t in ("Rust Engineer", "Head of Growth", "Senior Data Analyst") if t in text}

    assert titles(role="data") == {"Senior Data Analyst"}
    assert titles(seniority="head") == {"Head of Growth"}
    assert titles(country="SG") == {"Rust Engineer"}
    assert titles(remote="1") == {"Senior Data Analyst"}
    assert titles(remote="anywhere") == set()
    assert titles(salary="1") == {"Senior Data Analyst"}
    assert titles(exclude="growth") == {"Rust Engineer", "Senior Data Analyst"}


def test_sector_override_from_companies_page(client, tmp_path):
    page = client.get("/companies").text
    assert "Delta Bank" in page and "Not crypto" in page
    delta = client.get("/", params={"sector": "all", "role": "data"}).text
    job_id = delta.split('hx-get="/jobs/')[1].split('"')[0]
    company_id = client.get(f"/jobs/{job_id}").text.split("/?company=")[1].split("&")[0].split('"')[0]
    r = client.post(f"/companies/{company_id}/sector/crypto")
    assert r.status_code == 200 and "Crypto" in r.text
    assert "Senior Data Analyst" in client.get("/").text
    assert "Delta Bank,crypto,ui" in (tmp_path / "company_sectors.csv").read_text()
    assert client.post(f"/companies/{company_id}/sector/maybe").status_code == 400


@pytest.fixture
def shortlisted(tmp_path):
    from jobradar.match import import_results
    db = tmp_path / "sl.db"
    conn = connect(db)
    ingest(conn, [Posting(source="cryptojobslist", source_job_id=str(i), company=c, title=t, posted_at=now_iso(),
                          locations=["Remote"], remote=True) for i, (c, t) in enumerate(
        [("Saifuro", "Product Manager"), ("Accountable", "Junior Backend Engineer")])])
    ids = dict(conn.execute("SELECT c.name, j.id FROM jobs j JOIN companies c ON c.id = j.company_id").fetchall())
    import_results(conn, [
        {"job_id": ids["Saifuro"], "verdict": "apply_now", "track": "product", "rec": 77, "hm": 72, "want": 90,
         "why": "agent payments", "risk": "check country", "start_cv": "OneKey Web3 PM"},
        {"job_id": ids["Accountable"], "verdict": "stretch", "track": "backend", "rec": 65, "hm": 55, "want": 75,
         "why": "junior backend", "risk": "Java", "start_cv": "Limitless Product Engineer"}], run="test")
    conn.close()
    return TestClient(create_app(db, sectors_csv=tmp_path / "s.csv")), ids


def test_shortlist_groups_by_verdict(shortlisted):
    client, _ = shortlisted
    page = client.get("/shortlist").text
    assert page.index("<h2>Apply now") < page.index("Product Manager") < page.index("<h2>Stretch") < page.index("Junior Backend")
    assert page.index("Want <b>90</b>") < page.index("HM <b>72</b>") < page.index("Rec 77") and "Base CV: OneKey Web3 PM" in page and "Scored by hand" in page
    assert 'Shortlist <span class="count">2</span>' in page


def test_label_saves_filters_and_clears(shortlisted):
    client, ids = shortlisted
    r = client.post(f"/shortlist/{ids['Saifuro']}/label", data={"label": "Y", "note": "love it"})
    assert r.status_code == 200 and 'value="Y" checked' in r.text and "love it" in r.text
    page = client.get("/shortlist", params={"unlabelled": "1"}).text
    assert "Junior Backend" in page and "Product Manager" not in page
    assert 'Shortlist <span class="count">1</span>' in page
    client.post(f"/shortlist/{ids['Saifuro']}/label", data={"label": "", "note": "love it"})
    assert "Product Manager" in client.get("/shortlist", params={"unlabelled": "1"}).text


def test_label_rejects_bad_values(shortlisted):
    client, ids = shortlisted
    assert client.post(f"/shortlist/{ids['Saifuro']}/label", data={"label": "yes"}).status_code == 400
    assert client.post("/shortlist/99999/label", data={"label": "Y"}).status_code == 404
