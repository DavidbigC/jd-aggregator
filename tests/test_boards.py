from jobradar.collectors import feeds, web3career


def _valid(ps, source):
    for p in ps:
        assert p.source == source and p.source_job_id and p.title and p.company and p.url


def test_web3career_rows(http):
    ps = web3career.collect(http, pages=1)
    assert len(ps) >= 10
    _valid(ps, "web3career")
    assert all(p.url.startswith("https://web3.career/") for p in ps)


def test_cryptojobslist_has_company_and_full_description(http):
    ps = feeds.cryptojobslist(http)
    assert len(ps) >= 50
    _valid(ps, "cryptojobslist")
    assert all(p.company != "Unknown" for p in ps)
    assert sum(bool(p.description and len(p.description) > 300) for p in ps) > len(ps) / 2


def test_role_at_company_feeds(http):
    for fn, source in ((feeds.cryptocurrencyjobs, "cryptocurrencyjobs"), (feeds.web3vacancy, "web3vacancy"),
                       (feeds.cryptojobs, "cryptojobs")):
        ps = fn(http)
        assert ps, source
        _valid(ps, source)
        assert sum(p.company != "Unknown" for p in ps) > len(ps) * 0.8


def test_eleduck_keeps_only_web3_posts(http):
    ps = feeds.eleduck(http)
    _valid(ps, "eleduck")
    assert all(feeds.WEB3_WORDS.search(p.title + " " + (p.description or "")) for p in ps)


def test_role_split():
    assert feeds._role_at_company("Senior Frontend Engineer, Portfolio at Coinbase") == ("Senior Frontend Engineer, Portfolio", "Coinbase")
    assert feeds._role_at_company("Data Engineer") == ("Data Engineer", "Unknown")
