from jobradar.normalize import (ats_board_from_url, ats_key_from_url, company_key, html_to_text,
                                regions_for, is_remote, shingles, similarity, title_key, to_iso, url_key)


def test_company_key_strips_suffixes_and_applies_aliases():
    assert company_key("Payward, Inc.") == "kraken"
    assert company_key("Chainlink Labs") == company_key("Chainlink") == "chainlink"
    assert company_key("Crypto.com") == "crypto com"
    assert company_key("Foris DAX") == "crypto com"
    assert company_key("未具名 (Rebase)") == "未具名"


def test_title_key_drops_location_and_work_mode_segments():
    assert title_key("Risk Manager, Quantitative - EMEA") == "risk manager quantitative"
    assert title_key("Risk Manager, Quantitative – United States") == "risk manager quantitative"
    assert title_key("Sr. Software Engineer (Remote)") == "senior software engineer"
    assert title_key("Head of Asia Partnerships") == "head of asia partnerships"
    assert title_key("Full-Stack Engineer") == "full stack engineer"
    assert title_key("高级 - 运营负责人") == "高级 运营负责人"
    assert title_key("Rust工程师, 远程") == "rust工程师"


def test_regions_and_remote():
    assert regions_for(["Singapore"]) == ["APAC"]
    assert regions_for(["Remote - EMEA", "New York, NY"]) == ["EMEA", "Americas"]
    assert regions_for(["Australia"]) == ["APAC"]
    assert regions_for(["香港"]) == ["APAC"]
    assert is_remote(["Remote (US)"]) and not is_remote(["London"])


def test_to_iso_handles_every_format_seen_in_sources():
    assert to_iso("2026-09-08T18:53:27-04:00") == "2026-09-08T22:53:27Z"
    assert to_iso("2026-10-16T10:44:16.327+00:00") == "2026-10-16T10:44:16Z"
    assert to_iso("2026-10-20 16:28:43 UTC") == "2026-10-20T16:28:43Z"
    assert to_iso("2026-10-21 06:11:58 +0100") == "2026-10-21T05:11:58Z"
    assert to_iso("Tue, 20 Oct 2026 08:00:00 +0200") == "2026-10-20T06:00:00Z"
    assert to_iso("2026-06-26") == "2026-06-26T00:00:00Z"
    assert to_iso(1792574068861) == to_iso(1792574068)
    assert to_iso("Posted 6 Days Ago") is None


def test_html_to_text_handles_double_escaped_greenhouse_content():
    assert html_to_text("&lt;p&gt;Hello &amp;amp; welcome&lt;/p&gt;&lt;ul&gt;&lt;li&gt;Rust&lt;/li&gt;&lt;/ul&gt;") == "Hello & welcome\n\n• Rust"


def test_ats_keys_and_url_keys():
    assert ats_key_from_url("https://www.coinbase.com/careers/positions/8289787?gh_jid=8289787") == "gh:8289787"
    assert ats_key_from_url("https://job-boards.greenhouse.io/okx/jobs/123") == "gh:123"
    assert ats_key_from_url("https://jobs.ashbyhq.com/kraken.com/993557d9-7482-4f63-aae0-5817998b2368") == "ashby:993557d9-7482-4f63-aae0-5817998b2368"
    assert ats_key_from_url("https://jobs.lever.co/crypto/01670d38-387b-4ff7-af1a-075adfde484a/apply") == "lever:01670d38-387b-4ff7-af1a-075adfde484a"
    assert ats_key_from_url("https://apply.workable.com/j/DAEE9DFB86") == "workable:DAEE9DFB86"
    assert ats_key_from_url("https://careers.coindcx.com/opportunities/jd?id=5") is None
    assert url_key("https://www.careers.coindcx.com/opportunities/jd?id=5&utm_source=x") == "careers.coindcx.com/opportunities/jd?id=5"


def test_ats_board_from_url():
    assert ats_board_from_url("https://jobs.ashbyhq.com/kraken.com/993557d9-7482-4f63-aae0-5817998b2368") == ("ashby", "kraken.com")
    assert ats_board_from_url("https://job-boards.eu.greenhouse.io/gsrmarkets/jobs/1") == ("greenhouse", "gsrmarkets")
    assert ats_board_from_url("https://jobs.eu.lever.co/aavelabs/x") == ("lever-eu", "aavelabs")
    assert ats_board_from_url("https://tether.recruitee.com/o/x") == ("recruitee", "tether")
    assert ats_board_from_url("https://circle.wd1.myworkdayjobs.com/en-US/circle/job/x") == ("workday", "circle|wd1|circle")
    assert ats_board_from_url("https://boards.greenhouse.io/embed/job_app?for=x") is None
    assert ats_board_from_url("https://foo.com/careers") is None


def test_similarity_separates_copies_from_different_jobs():
    base = " ".join(f"word{i}" for i in range(200))
    a = shingles(base)
    b = shingles(base + " singapore office")
    c = shingles(" ".join(f"other{i}" for i in range(200)))
    truncated = shingles(" ".join(f"word{i}" for i in range(60)))
    assert similarity(a, b) >= 0.85
    assert similarity(a, c) < 0.2
    assert similarity(a, truncated) >= 0.85
    assert similarity(a, set()) == 0.0
