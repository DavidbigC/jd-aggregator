from pathlib import Path

from jd_aggregator import detail

FX = Path(__file__).parent / "fixtures"


def page(name: str) -> str:
    return (FX / f"detail_{name}.html").read_text()


def test_jsonld_jobposting_fields():
    d = detail.parse(page("cryptojobslist"))
    assert d.title == "Quantitative Developer - Options Pricing" and d.company == "Paradex"
    assert d.posted_at == "2026-10-05T06:52:23Z" and len(d.description) > 1000


def test_jsonld_from_workday_getro_and_habr():
    wd, gt, hb = detail.parse(page("workday")), detail.parse(page("getro")), detail.parse(page("habr"))
    assert wd.posted_at.startswith("2026-10-21") and len(wd.description) > 1000
    assert gt.company == "Anchorage Digital" and len(gt.description) > 3000
    assert "Blockchain" in hb.title and hb.company == "Bitbanker.ru"


def test_falls_back_to_main_text_without_jsonld():
    d = detail.parse(page("foresight"))
    assert d.title and d.description and len(d.description) > 100


def test_known_container_and_salary():
    html = ('<h1>Rust Engineer</h1><div class="show-more-less-html__markup relative">'
            '<p>Build matching engines.</p><ul><li>Rust</li></ul></div>')
    d = detail.parse(html)
    assert d.title == "Rust Engineer" and d.description == "Build matching engines.\n\n• Rust"
    ld = ('<script type="application/ld+json">{"@type":"JobPosting","title":"T","jobLocationType":"TELECOMMUTE",'
          '"baseSalary":{"currency":"USD","value":{"minValue":"120000","maxValue":160000,"unitText":"YEAR"}}}</script>')
    d = detail.parse(ld)
    assert d.salary == "USD 120k–160k / year" and d.remote and d.locations == ["Remote"]
