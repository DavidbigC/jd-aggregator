from jd_aggregator.models import Posting
from jd_aggregator.registry import discover_boards, load_seed


def test_load_seed_creates_companies_and_boards_once(conn, tmp_path):
    seed = tmp_path / "boards.csv"
    seed.write_text("company,website,ats,slug,origin,enabled\n"
                    "Kraken,https://kraken.com,ashby,kraken.com,verified,1\n"
                    "Drift Protocol,,notion,driftprotocol,research,0\n")
    assert load_seed(conn, seed) == 2
    rows = conn.execute("SELECT c.name, b.ats, b.enabled FROM boards b JOIN companies c ON c.id = b.company_id "
                        "ORDER BY b.id").fetchall()
    assert [tuple(r) for r in rows] == [("Kraken", "ashby", 1), ("Drift Protocol", "notion", 0)]
    assert load_seed(conn, seed) == 0


def test_discover_boards_from_aggregator_urls(conn):
    ps = [Posting(source="getro:x", source_job_id="1", company="Payward, Inc.", title="Eng",
                  url="https://jobs.ashbyhq.com/kraken.com/993557d9-7482-4f63-aae0-5817998b2368"),
          Posting(source="getro:x", source_job_id="2", company="Foo", title="Eng", url="https://foo.com/careers/1"),
          Posting(source="getro:x", source_job_id="3", company="Drift", title="Eng", url="https://drift.notion.site/x")]
    assert discover_boards(conn, ps) == 1
    row = conn.execute("SELECT c.key, b.ats, b.slug, b.origin FROM boards b JOIN companies c ON c.id = b.company_id")
    assert tuple(row.fetchone()) == ("kraken", "ashby", "kraken.com", "discovered")


def test_discover_skips_boards_that_differ_only_by_case(conn):
    conn.execute("INSERT INTO companies (key, name, created_at) VALUES ('bullish', 'Bullish', '2026-10-21T00:00:00Z')")
    conn.execute("INSERT INTO boards (company_id, ats, slug, origin) VALUES (1, 'workday', 'bullish|wd3|bullish', 'seed')")
    p = Posting(source="getro:x", source_job_id="1", company="Bullish", title="Eng",
                url="https://bullish.wd3.myworkdayjobs.com/en-US/Bullish/job/HK/Eng_R1")
    assert discover_boards(conn, [p]) == 0


def test_load_seed_reads_crypto_only(conn, tmp_path):
    seed = tmp_path / "boards.csv"
    seed.write_text("company,website,ats,slug,origin,enabled,crypto_only\n"
                    "DBS,,workday,dbs|wd3|dbs_careers,research,1,1\n")
    load_seed(conn, seed)
    assert conn.execute("SELECT crypto_only FROM boards").fetchone()[0] == 1
