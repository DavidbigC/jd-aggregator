import json

from jobradar.ingest import ingest
from jobradar.models import Posting

T0, T1 = "2026-10-21T00:00:00Z", "2026-10-21T06:00:00Z"
JD = " ".join(f"duty{i}" for i in range(300))
OTHER_JD = " ".join(f"compliance{i}" for i in range(300))


def P(**kw):
    base = dict(source="s", source_job_id="1", company="Acme", title="Engineer")
    base.update(kw)
    return Posting(**base)


def jobs(conn):
    return conn.execute("SELECT * FROM jobs ORDER BY id").fetchall()


def n_sightings(conn):
    return conn.execute("SELECT COUNT(*) FROM sightings").fetchone()[0]


def test_same_ats_id_across_sources_is_one_job(conn):
    ingest(conn, [P(source="ats:greenhouse:acme", source_job_id="77", url="https://boards.greenhouse.io/acme/jobs/77",
                    description=JD, from_ats=True)], now=T0)
    ingest(conn, [P(source="getro:dragonfly", source_job_id="g1", title="Something Else",
                    url="https://acme.com/careers?gh_jid=77")], now=T0)
    assert len(jobs(conn)) == 1 and n_sightings(conn) == 2


def test_per_city_copies_merge_and_keep_all_locations(conn):
    ingest(conn, [P(source="ats:ashby:acme", source_job_id="a", locations=["London"], description=JD, from_ats=True),
                  P(source="ats:ashby:acme", source_job_id="b", locations=["Singapore"], description=JD + " singapore",
                    from_ats=True)], now=T0)
    (j,) = jobs(conn)
    assert json.loads(j["locations"]) == ["London", "Singapore"]
    assert json.loads(j["regions"]) == ["APAC", "EMEA"]


def test_same_title_with_different_description_stays_separate(conn):
    ingest(conn, [P(source_job_id="a", description=JD), P(source_job_id="b", description=OTHER_JD)], now=T0)
    assert len(jobs(conn)) == 2


def test_board_copy_without_description_attaches_as_probable(conn):
    ingest(conn, [P(source="ats:lever:acme", source_job_id="a", description=JD, from_ats=True)], now=T0)
    ingest(conn, [P(source="cryptojobslist", source_job_id="cjl-1", title="Engineer (Remote)")], now=T0)
    assert len(jobs(conn)) == 1
    assert conn.execute("SELECT match FROM sightings WHERE source = 'cryptojobslist'").fetchone()[0] == "probable"


def test_resighting_only_moves_last_seen(conn):
    ingest(conn, [P()], now=T0)
    stats = ingest(conn, [P()], now=T1)
    (j,) = jobs(conn)
    assert (j["first_seen_at"], j["last_seen_at"]) == (T0, T1)
    assert n_sightings(conn) == 1 and stats["new_jobs"] == 0


def test_ats_description_replaces_truncated_board_copy(conn):
    ingest(conn, [P(source="cryptojobslist", source_job_id="c", description=" ".join(JD.split()[:80]))], now=T0)
    ingest(conn, [P(source="ats:greenhouse:acme", source_job_id="9", description=JD, from_ats=True,
                    url="https://boards.greenhouse.io/acme/jobs/9")], now=T1)
    (j,) = jobs(conn)
    assert j["description"] == JD and j["desc_from_ats"] == 1
    assert j["apply_url"] == "https://boards.greenhouse.io/acme/jobs/9"


def test_company_aliases_merge_legal_names(conn):
    ingest(conn, [P(company="Kraken", source_job_id="a", description=JD),
                  P(company="Payward, Inc.", source="jobstash", source_job_id="b", description=JD)], now=T0)
    assert len(jobs(conn)) == 1
    assert conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0] == 1


def test_same_generic_url_does_not_merge_different_titles(conn):
    url = "https://careers.coindcx.com/opportunities/jd"
    ingest(conn, [P(company="CoinDCX", title="Key Accounts Manager", source_job_id="1", url=url),
                  P(company="CoinDCX", title="Senior Manager Analytics", source_job_id="2", url=url)], now=T0)
    assert len(jobs(conn)) == 2


def test_fts_index_is_searchable(conn):
    ingest(conn, [P(title="Rust Engineer", description="low latency matching engine")], now=T0)
    assert conn.execute("SELECT rowid FROM jobs_fts WHERE jobs_fts MATCH '\"matching\"'").fetchone() is not None


def test_undated_new_job_gets_a_date_only_when_the_source_was_polled_before(conn):
    ingest(conn, [P(source_job_id="1")], T0)
    ingest(conn, [P(source_job_id="2", title="Designer")], T1, trust_new=True)
    dates = dict(conn.execute("SELECT title, posted_at FROM jobs").fetchall())
    assert dates == {"Engineer": None, "Designer": T1}
