import pytest

from jd_aggregator.collectors import ats
from jd_aggregator.config import SUPPORTED_ATS

CASES = [
    ("greenhouse", "flowdesk", "gh:"), ("lever", "ethena", "lever:"), ("lever-eu", "aavelabs", "lever:"),
    ("ashby", "keyrock", "ashby:"), ("workable", "chaingpt", "workable:"), ("recruitee", "bitfinex", None),
    ("smartrecruiters", "coinstats", None), ("bamboohr", "fusang", None), ("breezy", "zero-hash", None),
    ("teamtailor", "spiko", None), ("personio", "finoa", None), ("rippling", "halborn-inc", None),
    ("gem", "agora", None), ("workday", "bullish|wd3|bullish", None),
]
WITH_DESCRIPTION = {"greenhouse", "lever", "lever-eu", "ashby", "workable", "recruitee", "teamtailor", "gem"}


def test_adapters_match_supported_list():
    assert set(ats.ADAPTERS) == SUPPORTED_ATS


@pytest.mark.parametrize("name,slug,key_prefix", CASES)
def test_adapter_parses_recorded_board(http, name, slug, key_prefix):
    ps = ats.ADAPTERS[name](http, slug, "TestCo")
    assert ps, "fixture has no jobs: re-record with another board of this ATS"
    for p in ps:
        assert p.source == f"ats:{name}:{slug}" and p.company == "TestCo" and p.from_ats
        assert p.source_job_id and p.title and p.url
        if key_prefix:
            assert p.ats_key.startswith(key_prefix)
    if name in WITH_DESCRIPTION:
        assert any(p.description and len(p.description) > 200 for p in ps)
