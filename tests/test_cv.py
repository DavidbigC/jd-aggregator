import json
import time

import pytest
from fastapi.testclient import TestClient

from jd_aggregator import deepseek, keystore
from jd_aggregator.cv import CONTACT, pdf, set_setting, sources, tailor
from jd_aggregator.cv import runner as cvs
from jd_aggregator.web import app as web
from jd_aggregator.db import connect
from jd_aggregator.ingest import ingest
from jd_aggregator.match import import_results
from jd_aggregator.models import Posting
from jd_aggregator.normalize import now_iso
from jd_aggregator.web.app import create_app

REAL_RENDER = pdf.render
AD = "Analyse on-chain and product data with SQL and Python for our DeFi app. Remote, worldwide. " * 10
CONTACT_LINE = "+44 7700 900123 · david@example.com · Somewhere"


def _cv(**kw):
    base = {"language": "en", "headline": "Crypto Data Analyst — product and on-chain analytics",
            "summary": "5+ years in crypto; ran the retention analysis behind a 25% gain.",
            "skills": [{"group": "Analytics", "items": ["SQL (DuneSQL, PostgreSQL)", "**Python**"]}],
            "experience": [{"org": "Independent", "title": "On-Chain Market Maker & Arbitrageur",
                            "dates": "2021 – Present", "bullets": ["Full-time since May 2026; sets strategy and risk"]},
                           {"org": "FLOKI", "title": "Data Analyst", "dates": "Dec 2024 – Apr 2026",
                            "bullets": ["- Owned the product database powering BI and dashboards"] * 7},
                           {"org": "Elfin Metaverse (Dragon Race)", "title": "Operation & Data Analyst",
                            "dates": "May 2024 – Mar 2025", "bullets": ["Improved next-month retention by 25%"]},
                           {"org": "CARV", "title": "Community Lead", "dates": "2022 – 2023", "bullets": ["a"] * 7}],
            "projects": [{"name": "FLOKI BSC Transaction Warehouse", "dates": "2025", "link": "not a url",
                          "bullets": ["Built a BNB Chain warehouse"]}],
            "highlights": ["Submitted Dune Spellbook dbt PRs"],
            "education": [{"degree": "MSc Research Methods", "school": "University of Glasgow", "year": "2024"}],
            "notes": "Led with retention."}
    return {**base, **kw}


REVIEW = {"score": 72, "would_shortlist": False, "verdict": "Good proof, summary too generic.",
          "issues": [{"severity": "should_fix", "where": "CARV", "problem": "Vague", "fix": "Add the 200% number"},
                     {"severity": "must_fix", "where": "Summary", "problem": "Bury the lead", "fix": "Lead with Dune"}],
          "missing_keywords": ["cohort analysis"], "invented_claims": []}


def test_pack_scrubs_private_details(tmp_path):
    src = tmp_path / "cv"
    (src / "projects").mkdir(parents=True)
    (src / "README.md").write_text("# David\n**GitHub:** [g](https://github.com/x)\n**X:** [@x](https://x.com/x)\n"
                                   "call +44 7700 900123\nmail me at a@b.com\n"
                                   "## Converting a Markdown CV to PDF\nnpm install\n## Short Summary\n- kept line\n")
    (src / "experience.md").write_text("- ranked 7th of 71 accounts above $1M volume\n"
                                       "- 25.8% APR since start, ~80% spread, reconciled to equity within $3\n"
                                       "- P&L $5,200 on $21.2k capital\n")
    (src / "skills.md").write_text("- SQL\n")
    (src / "projects" / "a.md").write_text("- near-ATM calls (+$100–$300) collect real premium\n")
    pack = sources.build(src)
    assert "above $1M volume" in pack and "25.8% APR since start, ~80% spread" in pack
    assert "within $3" not in pack and "5,200" not in pack and "21.2k" not in pack and "(+$100" not in pack
    assert "7700" not in pack and "a@b.com" not in pack and "npm install" not in pack and "kept line" in pack
    assert "near-ATM calls collect real premium" in pack and "<!-- file: projects/a.md -->" in pack
    assert sources.links(pack) == [("GitHub", "https://github.com/x"), ("X", "https://x.com/x")]


def test_committed_pack_is_clean():
    pack = sources.PACK.read_text()
    assert not sources.money(pack) and not sources.EMAIL.search(pack) and not sources.PHONE.search(pack)
    assert "Ultra CV Master" not in pack
    assert [k for k, _ in sources.links(pack)][:2] == ["GitHub", "Website"]


def test_clean_cv_caps_and_strips_markdown():
    cv = tailor.clean_cv(_cv(language="fr"))
    assert cv["language"] == "en"
    assert cv["skills"][0]["items"] == ["SQL (DuneSQL, PostgreSQL)", "Python"]
    assert len(cv["experience"][1]["bullets"]) == 5 and len(cv["experience"][3]["bullets"]) == 5
    assert cv["experience"][1]["bullets"][0].startswith("Owned")
    assert cv["projects"][0]["link"] is None
    solo = {"org": "Independent Builder", "title": "independent builder", "dates": "2021 – Present", "bullets": ["b"]}
    assert tailor.clean_cv(_cv(experience=[solo]))["experience"][0]["title"] == ""
    stutter = {**solo, "org": "Independent", "title": "Independent On-Chain Market Maker & Arbitrageur"}
    e = tailor.clean_cv(_cv(experience=[stutter]))["experience"][0]
    assert (e["org"], e["title"]) == ("Independent On-Chain Market Maker & Arbitrageur", "")
    with pytest.raises(ValueError):
        tailor.clean_cv({"experience": [{"org": "FLOKI", "bullets": []}]})


@pytest.mark.parametrize("change, problem", [
    ({}, None),
    ({"summary": "Reach me at d@x.com"}, "email"),
    ({"summary": "Call +44 7700 900123"}, "phone"),
    ({"summary": "Made $5,200 trading"}, "dollar"),
    ({"summary": "He built dashboards"}, "pronoun"),
    ({"summary": "他负责数据分析"}, "pronoun"),
    ({"highlights": ["Spellbook PRs merged into main"]}, "merged"),
    ({"experience": [{"org": "FLOKI", "title": "x", "dates": "x", "bullets": ["b"]}]}, "Dragon Race"),
    ({"experience": _cv()["experience"][1:]}, "Independent On-Chain Market Maker"),
    ({"experience": [{**e, "dates": "Dec 2024 – Present"} if e["org"] == "FLOKI" else e for e in _cv()["experience"]]},
     "FLOKI as current"),
    ({"summary": "Currently a data analyst at FLOKI."}, "FLOKI current"),
    ({"highlights": ["Submitted Spellbook PRs (not merged)"]}, "sells against"),
    ({"summary": "Ran it (团队成果)"}, "sells against"),
    ({"headline": "Crypto trader and data analyst"}, "trader"),
    ({"skills": [{"group": "AI", "items": ["Writing briefs, specs and decision summaries for agents"]}]}, "at most 4 words"),
    ({"projects": [{"name": "Retention study", "bullets": ["Found the 25% next-month lift"]}]}, "25%"),
    ({"experience": [{**e, "bullets": ["word " * 59] * 5} for e in _cv()["experience"]]}, "too long"),
])
def test_problems(change, problem):
    found = tailor.problems(tailor.clean_cv(_cv(**change)))
    assert (problem is None and not found) or (problem and any(problem in f for f in found))
    fine = "其他项目; ranked above $1M volume; 25% retention; a terminal for traders; presented to the team at FLOKI"
    assert not tailor.problems(tailor.clean_cv(_cv(summary=fine)))
    years = tailor.clean_cv(_cv(summary="5+ years in crypto analytics."))
    assert any("asks for 6+" in f for f in tailor.problems(years, "Requirements: 6+ years of product analytics; 2 years of dbt"))
    assert not tailor.problems(years, "3+ years of SQL") and not tailor.problems(years)
    assert not tailor.problems(tailor.clean_cv(_cv(skills=[{"group": "AI", "items": [
        "Directing AI coding agents (Claude Code, Codex)", "SQL (DuneSQL, PostgreSQL, SQLite)"]}])))


def test_markdown_follows_the_devmaster_layout():
    md = tailor.to_markdown(tailor.clean_cv(_cv()), CONTACT_LINE, [("GitHub", "https://github.com/x")])
    assert md.startswith("# David Chen\n\n**Crypto Data Analyst")
    assert f"{CONTACT_LINE}  \n[GitHub](https://github.com/x)" in md
    assert "## Core Skills\n\n**Analytics:** SQL (DuneSQL, PostgreSQL), Python" in md
    assert "### Independent | On-Chain Market Maker & Arbitrageur | 2021 – Present\n\n- Full-time" in md
    assert "### FLOKI | Data Analyst | Dec 2024 – Apr 2026\n\n- Owned" in md
    assert "**MSc Research Methods** — University of Glasgow | 2024" in md
    zh = tailor.to_markdown(tailor.clean_cv(_cv(language="zh")), "", [])
    assert "## 工作经历" in zh and "  \n" not in zh.split("## ")[0]


@pytest.fixture
def fake_deepseek(monkeypatch):
    calls = []
    replies = {"write": [_cv()], "review": [REVIEW]}

    def fake_chat(key, messages, **kw):
        calls.append(messages)
        kind = "review" if "in-house recruiter" in messages[0]["content"] else "write"
        queue = replies[kind]
        data = queue.pop(0) if len(queue) > 1 else queue[0]
        return data, {"prompt_cache_hit_tokens": 25000, "prompt_cache_miss_tokens": 3000, "completion_tokens": 5000}

    monkeypatch.setattr(deepseek, "chat_json", fake_chat)
    return calls, replies


def _job():
    return {"title": "Product Data Analyst", "company": "Kamino", "locations": ["Remote"], "description": AD}


def test_tailor_runs_four_passes_with_a_stable_prefix(fake_deepseek):
    calls, replies = fake_deepseek
    replies["review"] = [REVIEW, {**REVIEW, "score": 81, "issues": []}]
    out = tailor.tailor("sk-x", _job(), {"lead_with": ["Dragon Race retention +25%"], "scores": {"want": 90}})
    assert len(calls) == 4 and out["review"]["score"] == 72 and out["review"]["would_shortlist"] is True
    assert out["final_review"]["score"] == 81 and out["final"]["headline"] in calls[3][1]["content"]
    assert "Led with retention." not in calls[1][1]["content"] + calls[3][1]["content"]
    assert out["review"]["issues"][0]["severity"] == "must_fix"
    pack = sources.PACK.read_text()
    assert all(c[0]["content"].startswith(pack) for c in calls)
    assert calls[0][0] == calls[2][0]
    assert "Dragon Race retention +25%" in calls[0][1]["content"] and '"want"' not in calls[0][1]["content"]
    assert "Recruiter review (json)" in calls[2][1]["content"]


def test_a_failed_final_screen_gets_one_repair(fake_deepseek):
    calls, replies = fake_deepseek
    flagged = {**REVIEW, "score": 90, "issues": [], "invented_claims": ["decision memos"]}
    replies["review"] = [REVIEW, flagged, {**REVIEW, "score": 80, "issues": []}, flagged]
    out = tailor.tailor("sk-x", _job(), None)
    assert len(calls) == 6 and out["final_review"]["score"] == 80
    assert "decision memos" in calls[4][1]["content"]
    replies["review"] = [REVIEW, flagged]
    replies["write"] = [_cv(), _cv(), _cv(summary="He did it")]
    out = tailor.tailor("sk-x", _job(), None)
    assert out["final_review"]["score"] == 40 and out["final"]["summary"] == _cv()["summary"]


def test_tailor_retries_once_on_a_leak_then_fails(fake_deepseek):
    calls, replies = fake_deepseek
    replies["write"] = [_cv(summary="He did it"), _cv()]
    tailor.tailor("sk-x", _job(), None)
    assert len(calls) == 7 and "pronoun 'He'" in calls[1][-1]["content"]
    replies["write"] = [_cv(summary="mail d@x.com")]
    with pytest.raises(ValueError, match="email"):
        tailor.tailor("sk-x", _job(), None)


@pytest.fixture
def app(tmp_path, monkeypatch, fake_deepseek):
    monkeypatch.setattr(keystore, "get_key", lambda: ("sk-test0123456789abcdef", "keychain"))
    db = tmp_path / "cv.db"
    conn = connect(db)
    ingest(conn, [Posting(source="cryptojobslist", source_job_id=str(i), company=c, title=t, posted_at=now_iso(),
                          locations=["Remote (Anywhere)"], remote=True, description=AD)
                  for i, (c, t) in enumerate([("Kamino", "Product Data Analyst"), ("Dune", "On-chain Analyst")])])
    ids = dict(conn.execute("SELECT c.name, j.id FROM jobs j JOIN companies c ON c.id = j.company_id").fetchall())
    import_results(conn, [{"job_id": i, "verdict": "apply_now", "rec": 70, "hm": 70, "want": 70,
                           "result": json.dumps({"lead_with": ["x"]})} for i in ids.values()], run="t")
    conn.close()
    return TestClient(create_app(db, sectors_csv=tmp_path / "s.csv")), db, ids, fake_deepseek[0]


def _wait():
    for _ in range(200):
        with cvs._lock:
            if not cvs._active:
                return
        time.sleep(0.02)


def test_job_pane_tailors_and_shows_the_cv(app):
    client, db, ids, calls = app
    kamino = ids["Kamino"]
    page = client.get(f"/jobs/{kamino}", headers={"HX-Request": "true"}).text
    assert "Tailor my CV for this job" in page and "never sent to DeepSeek" in page
    assert client.get(f"/jobs/{kamino}/cv").status_code == 404

    client.post("/settings/cv-contact", data={"contact": CONTACT_LINE})
    client.post(f"/jobs/{kamino}/cv")
    _wait()
    assert all(CONTACT_LINE not in m["content"] and "7700" not in m["content"] for c in calls for m in c)
    section = client.get(f"/jobs/{kamino}/cv/section").text
    assert "Recruiter screen of this CV: <b>72/100</b>" in section and "(first draft 72)" in section
    assert "Still weak (2)" in section and "Bury the lead" in section and "Copy as Markdown" in section
    assert f'src="/jobs/{kamino}/cv?embed=1"' in section and "# David Chen" in section
    printed = client.get(f"/jobs/{kamino}/cv").text
    assert "<title>David Chen - Kamino Product Data Analyst</title>" in printed and "/static/resume.css" in printed
    assert "+44 7700 900123" in printed and "Print / Save as PDF" in printed
    assert "<h3>FLOKI | Data Analyst | Dec 2024 – Apr 2026</h3>" in printed
    assert "Print / Save as PDF" not in client.get(f"/jobs/{kamino}/cv?embed=1").text

    conn = connect(db)
    row = conn.execute("SELECT status, score, cost_usd, draft, final, final_review FROM tailored_cvs").fetchone()
    assert row["status"] == "done" and row["score"] == 72 and row["cost_usd"] > 0 and row["draft"] and row["final"]
    assert json.loads(row["final_review"])["score"] == 72


def test_failed_and_interrupted_cvs_show_an_error(app, fake_deepseek):
    client, db, ids, _ = app
    fake_deepseek[1]["write"] = [_cv(summary="mail d@x.com")]
    client.post(f"/jobs/{ids['Dune']}/cv")
    _wait()
    assert "The last attempt failed" in client.get(f"/jobs/{ids['Dune']}/cv/section").text
    conn = connect(db)
    conn.execute("INSERT INTO tailored_cvs (job_id, created_at, status, stage, model) VALUES (?, ?, 'running', 'writing', 'm')",
                 (ids["Kamino"], now_iso()))
    conn.commit()
    assert "Interrupted when the app restarted" in client.get(f"/jobs/{ids['Kamino']}/cv/section").text


def test_shortlist_batch_asks_then_tailors(app):
    client, db, ids, calls = app
    page = client.get("/shortlist").text
    assert "Tailor CVs for 2 shortlisted jobs" in page and calls == []
    assert "Tailor 2 CVs" in client.post("/shortlist/cv").text and calls == []
    client.post("/shortlist/cv/start")
    _wait()
    assert len(calls) == 12
    page = client.get("/shortlist").text
    assert "2 shortlisted jobs have a tailored CV" in page and page.count("CV ready</span>") == 2


def test_contact_line_is_saved_locally(app):
    client, db, *_ = app
    assert "Saved" in client.post("/settings/cv-contact", data={"contact": "  a   b "}).text
    assert 'value="a b"' in client.get("/settings").text
    set_setting(connect(db), CONTACT, "")
    assert 'value=""' in client.get("/settings").text


def test_flagged_claims_show_up_front(app, fake_deepseek):
    client, db, ids, _ = app
    flagged = {**REVIEW, "score": 90, "issues": [], "invented_claims": ["decision memos"]}
    fake_deepseek[1]["review"] = [REVIEW, flagged, flagged]
    client.post(f"/jobs/{ids['Dune']}/cv")
    _wait()
    section = client.get(f"/jobs/{ids['Dune']}/cv/section").text
    assert "<b>40/100</b>" in section and "Check before sending" in section and "(score capped at 40): decision memos" in section


def test_finished_cvs_are_saved_as_pdfs(app, cv_folder, monkeypatch):
    client, db, ids, _ = app
    opened = []
    monkeypatch.setattr(web.subprocess, "run", lambda args, **kw: opened.append(args))
    client.post("/settings/cv-contact", data={"contact": CONTACT_LINE})
    client.post(f"/jobs/{ids['Kamino']}/cv")
    _wait()
    saved = cv_folder / "David Chen - Kamino Product Data Analyst.pdf"
    body = saved.read_bytes().decode()
    assert body.startswith("%PDF") and CONTACT_LINE in body and "font-size: 9.5pt" in body and "Print / Save" not in body
    section = client.get(f"/jobs/{ids['Kamino']}/cv/section").text
    assert "Download PDF" in section and "PDF saved for uploading" in section and saved.name in section

    client.post("/settings/cv-contact", data={"contact": "+44 7700 900999"})
    r = client.get(f"/jobs/{ids['Kamino']}/cv.pdf")
    assert r.headers["content-type"] == "application/pdf" and "attachment" in r.headers["content-disposition"]
    assert "+44 7700 900999" in saved.read_text() and r.content == saved.read_bytes()
    assert client.get(f"/jobs/{ids['Dune']}/cv.pdf").status_code == 404

    assert client.post(f"/jobs/{ids['Kamino']}/cv/reveal").status_code == 204
    assert client.post("/cvs/folder").status_code == 204
    assert opened == [["open", "-R", str(saved)], ["open", str(cv_folder)]]
    assert "Every finished CV is saved as a PDF in" in client.get("/shortlist").text


def test_a_pdf_failure_keeps_the_cv(app, cv_folder, monkeypatch):
    client, db, ids, _ = app
    monkeypatch.setattr(pdf, "render", lambda html: 1 / 0)
    client.post(f"/jobs/{ids['Dune']}/cv")
    _wait()
    section = client.get(f"/jobs/{ids['Dune']}/cv/section").text
    assert "Recruiter screen of this CV" in section and "Download PDF saves it to" in section
    assert not cv_folder.exists()


def test_chromium_renders_a_cv_pdf():
    view = {"cv": {"final": tailor.clean_cv(_cv(language="zh", summary="链上数据分析师。"))}, "filename": "x",
            "contact": CONTACT_LINE, "links": []}
    out = REAL_RENDER(pdf.html(view))
    assert out.startswith(b"%PDF") and len(out) > 5000
