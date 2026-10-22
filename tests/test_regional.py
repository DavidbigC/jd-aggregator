from jobradar.collectors import mycareersfuture, rebase, telegram
from jobradar.config import INTERVALS
from jobradar.runner import SOURCES

DEJOB_EN = """#Recruitment
🏡  Temporal     #Research
🐇  Introduction:
https://www.temporal.xyz/
A crypto-native research & development firm.

🛵  #Full·Time #Remote #New·York (#USA #Remote)
📚  #Senior·Product·Engineer #Engineering
💰  Compensation: USD 200,000 - 250,000 / year"""

DEJOB_CN = """#招聘
🏡  Adam     #Headhunter
🛵  合作方式： #全职 #实地 #迪拜
📚  待招岗位：#运营负责人 #运营
💰  薪酬福利：USD 8000 - 12000 / 月，13薪"""

DIGEST = """- Ramp is hiring Product Operations Specialist | Procurement
- Kalshi is hiring Account Executive / Account Manager, Data Sales at Kalshi
- Robinhood is hiring Manager, Global Indirect Tax"""


def test_parse_dejob_english():
    (p,) = telegram.parse_dejob("DeJob_Global", "DeJob_Global/2545", DEJOB_EN, "2026-10-19T11:22:46Z")
    assert (p.company, p.title, p.remote) == ("Temporal", "Senior Product Engineer", True)
    assert p.locations == ["New York", "USA"] and p.salary == "USD 200,000 - 250,000 / year"
    assert p.url == "https://t.me/DeJob_Global/2545"


def test_parse_dejob_chinese():
    (p,) = telegram.parse_dejob("DeJob_official", "DeJob_official/8678", DEJOB_CN, None)
    assert (p.company, p.title, p.locations) == ("Adam", "运营负责人", ["迪拜"])


def test_non_job_posts_are_skipped():
    assert telegram.parse_dejob("DeJob_official", "x/1", "❤️请大家帮园长投上一票！", None) == []


def test_parse_digest():
    ps = telegram.parse_digest("web3hiring", "web3hiring/16557", DIGEST, None)
    assert [(p.company, p.title) for p in ps] == [
        ("Ramp", "Product Operations Specialist | Procurement"),
        ("Kalshi", "Account Executive / Account Manager, Data Sales"),
        ("Robinhood", "Manager, Global Indirect Tax"),
    ]
    assert len({p.source_job_id for p in ps}) == 3


def test_telegram_channels_from_fixtures(http):
    ps = telegram.collect(http)
    assert ps and all(p.source.startswith("telegram:") and p.title and p.company for p in ps)


def test_rebase_issues(http):
    ps = rebase.collect(http)
    assert ps and all(p.source == "rebase" and p.url.startswith("https://github.com/") for p in ps)
    assert any(p.locations for p in ps)


def test_mycareersfuture(http):
    ps = mycareersfuture.collect_term(http, "blockchain")
    assert ps and all(p.locations == ["Singapore"] and p.company != "Unknown" for p in ps)


def test_every_source_has_an_interval():
    assert set(SOURCES) == set(INTERVALS)
