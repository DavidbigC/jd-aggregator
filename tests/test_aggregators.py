import json
from pathlib import Path

from jd_aggregator.collectors import consider, getro, jobstash

FX = Path(__file__).parent / "fixtures"


def _valid(ps, prefix):
    assert ps
    for p in ps:
        assert p.source.startswith(prefix) and p.source_job_id and p.title and p.company and p.url


def test_jobstash_keeps_only_crypto_orgs(http):
    raw = json.loads((FX / "jobstash.json").read_text())["data"]
    expected = sum(1 for j in raw if (j.get("organization") or {}).get("isCrypto") and j.get("title"))
    ps = jobstash.collect(http)
    _valid(ps, "jobstash")
    assert len(ps) == expected
    assert any(p.ats_key for p in ps)


def test_getro_network(http):
    ps = getro.collect_network(http, "dragonfly")
    _valid(ps, "getro:dragonfly")
    assert len(ps) == 5 and all(p.detail_url.startswith("https://jobs.dragonfly.xyz/companies/") for p in ps)


def test_consider_board(http):
    ps = consider.collect_board(http, "pantera")
    _valid(ps, "consider:pantera")
    assert len(ps) == 5


def test_getro_takes_company_from_mismatched_linkedin_url():
    from jd_aggregator.collectors.getro import _company
    url = "https://www.linkedin.com/jobs/view/training-specialist-welding-fx-at-hadrian-4476623474"
    assert _company("StreamingFast", url) == "Hadrian"
    assert _company("Jump Trading", "https://www.linkedin.com/jobs/view/quant-at-jump-trading-123") == "Jump Trading"
    assert _company("Binance", "https://www.linkedin.com/jobs/view/analyst-at-binance-com-123") == "Binance"
    assert _company("Acme", "https://jobs.ashbyhq.com/acme/1") == "Acme"
