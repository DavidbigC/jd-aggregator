import pytest

from jd_aggregator.classify import classify_job, company_sectors, countries_for, remote_scope, sector_for
from jd_aggregator.ingest import ingest
from jd_aggregator.models import Posting
from jd_aggregator.normalize import is_web3


@pytest.mark.parametrize("title, role", [
    ("Senior Backend Engineer (Rust)", "engineering"),
    ("Data Engineer", "data"),
    ("Sales Engineer, APAC", "bd-sales"),
    ("Smart Contract Auditor", "security"),
    ("Quantitative Researcher", "quant-trading"),
    ("Research Analyst, Digital Assets", "research"),
    ("Compliance Analyst - AML", "compliance-legal-risk"),
    ("Product Designer", "design"),
    ("Senior Product Manager, Wallet", "product"),
    ("Head of Growth", "marketing-community"),
    ("Business Development Manager", "bd-sales"),
    ("Customer Support Specialist", "support"),
    ("Talent Acquisition Partner", "people"),
    ("Senior Accountant", "finance"),
    ("Executive Assistant to the CEO", "operations"),
    ("区块链开发工程师", "engineering"),
    ("社区运营", "marketing-community"),
    ("Разработчик блокчейн", "engineering"),
    ("블록체인 백엔드 개발자", "engineering"),
    ("Chef", "other"),
])
def test_role(title, role):
    assert classify_job(title, [], False)["role"] == role


@pytest.mark.parametrize("title, level", [
    ("Software Engineering Intern", "intern"),
    ("Junior Frontend Developer", "junior"),
    ("Backend Engineer", "mid"),
    ("Sr. Solidity Engineer", "senior"),
    ("Staff Engineer, Protocol", "lead"),
    ("Engineering Lead", "lead"),
    ("Head of Engineering", "head"),
    ("Senior Director, Compliance", "head"),
    ("VP of Marketing", "exec"),
    ("Chief Technology Officer", "exec"),
    ("资深后端工程师", "senior"),
    ("区块链实习生", "intern"),
])
def test_seniority(title, level):
    assert classify_job(title, [], False)["seniority"] == level


@pytest.mark.parametrize("locations, countries", [
    (["Remote - USA", "United States", "Remote"], ["US"]),
    (["New York, NY, USA"], ["US"]),
    (["Irvine, CA"], ["US"]),
    (["Bay Area, CA, US"], ["US"]),
    (["Vancouver, CA"], ["CA"]),
    (["台北市信義區, 台灣, TW"], ["TW"]),
    (["São Paulo, SP, BR"], ["BR"]),
    (["Москва, RU"], ["RU"]),
    (["강남구, 서울, 한국"], ["KR"]),
    (["London, United Kingdom", "Singapore"], ["GB", "SG"]),
    (["Sydney, New South Wales, Australia"], ["AU"]),
    (["Hong Kong SAR"], ["HK"]),
    (["Remote"], []),
])
def test_countries(locations, countries):
    assert countries_for(locations) == countries


@pytest.mark.parametrize("locations, scope", [
    (["Remote"], "anywhere"),
    (["Remote", "Remote (Earth)"], "anywhere"),
    (["Worldwide"], "anywhere"),
    (["Remote - USA", "United States"], "restricted"),
    (["Remote - European Region"], "restricted"),
    (["Remote (台灣)"], "restricted"),
])
def test_remote_scope(locations, scope):
    assert remote_scope(locations, countries_for(locations)) == scope


def test_remote_scope_only_for_remote_jobs():
    assert classify_job("Engineer", ["Remote"], False)["remote_scope"] is None


@pytest.mark.parametrize("text, hit", [
    ("Build restaking infrastructure", True),
    ("zk-proof systems engineer", True),
    ("Grow our DAO", True),
    ("Layer 2 scaling", True),
    ("Applied cryptography engineer", False),
    ("Tier 2 support", False),
])
def test_is_web3_protocol_terms(text, hit):
    assert is_web3(text) is hit


@pytest.mark.parametrize("args, sector", [
    (("Robinhood", True, True, 150, 40, 0, False), ("other", "crypto_only")),
    (("Coinbase", True, False, 200, 50, 0, False), ("crypto", "name")),
    (("Hyperithm", False, False, 29, 14, 2, True), ("crypto", "share")),
    (("Tenderly", True, False, 2, 0, 0, False), ("crypto", "seed")),
    (("Carta", True, False, 67, 0, 0, False), ("other", "default")),
    (("Reap", False, False, 18, 7, 0, True), ("crypto", "board")),
    (("Fidelity Investments", False, False, 36, 1, 0, True), ("other", "default")),
    (("Zscaler", False, False, 15, 0, 4, True), ("other", "default")),
])
def test_sector_rules(args, sector):
    assert sector_for(*args) == sector


def test_company_sectors_keeps_overrides(conn):
    ingest(conn, [Posting(source="jobstash", source_job_id="1", company="Defi Labs", title="Engineer"),
                  Posting(source="jobstash", source_job_id="2", company="Plain Co", title="Engineer"),
                  Posting(source="jobstash", source_job_id="3", company="Quiet Protocol", title="Engineer")])
    conn.execute("UPDATE companies SET sector = 'crypto', sector_source = 'override' WHERE name = 'Quiet Protocol'")
    company_sectors(conn)
    got = dict(conn.execute("SELECT name, sector FROM companies").fetchall())
    assert got == {"Defi Labs": "crypto", "Plain Co": "other", "Quiet Protocol": "crypto"}


def test_ingest_sets_job_fields(conn):
    ingest(conn, [Posting(source="jobstash", source_job_id="1", company="A", title="Senior Data Analyst",
                          locations=["Remote - USA"], remote=True)])
    j = conn.execute("SELECT role, seniority, countries, remote_scope FROM jobs").fetchone()
    assert tuple(j) == ("data", "senior", '["US"]', "restricted")


def test_sector_overrides_round_trip(conn, tmp_path):
    from jd_aggregator.registry import load_sectors, save_sector
    path = tmp_path / "company_sectors.csv"
    ingest(conn, [Posting(source="jobstash", source_job_id="1", company="Quiet Labs", title="Engineer")])
    save_sector(conn, path, 1, "crypto", "ui")
    conn.execute("UPDATE companies SET sector = NULL, sector_source = NULL")
    assert load_sectors(conn, path) == 1
    company_sectors(conn)
    assert tuple(conn.execute("SELECT sector, sector_source FROM companies").fetchone()) == ("crypto", "override")
