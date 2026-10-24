import json
import logging

from ..match import SHOWN
from ..normalize import now_iso
from . import CONTACT, get_setting, pdf, sources, tailor

log = logging.getLogger(__name__)
STAMP_KEYS = ("model", "prompt_version", "sources_hash")


def _row(r) -> dict:
    d = dict(r)
    for k in ("draft", "review", "final", "final_review"):
        d[k] = json.loads(d[k]) if d[k] else None
    return d


def latest(conn, job_id: int) -> dict | None:
    r = conn.execute("SELECT * FROM tailored_cvs WHERE job_id = ? ORDER BY id DESC LIMIT 1", (job_id,)).fetchone()
    return _row(r) if r else None


def is_stale(cv: dict, stamp: dict) -> bool:
    return any(cv[k] != stamp[k] for k in STAMP_KEYS)


def view(conn, job: dict) -> dict:
    """Everything the CV section and the print page need."""
    cv = latest(conn, job["id"])
    contact = get_setting(conn, CONTACT)
    out = {"cv": cv, "contact": contact, "stale": False, "markdown": "", "links": []}
    if cv and cv["status"] == "done":
        out["links"] = sources.links(sources.PACK.read_text())
        out["stale"] = is_stale(cv, tailor.stamps())
        out["markdown"] = tailor.to_markdown(cv["final"], contact, out["links"])
        out["filename"] = tailor.filename(job)
        out["pdf"] = pdf.location(out)
    return out


def ready(conn) -> set[int]:
    return {r[0] for r in conn.execute("SELECT DISTINCT job_id FROM tailored_cvs WHERE status = 'done'")}


def todo_ids(conn) -> list[int]:
    """Shortlisted jobs, best first, whose CV is missing or made with an older model, prompt or master CV."""
    stamp = tailor.stamps()
    ids = [r[0] for r in conn.execute(
        f"SELECT job_id FROM match_evaluations WHERE verdict IN ({', '.join('?' * len(SHOWN))}) "
        "ORDER BY priority DESC", SHOWN)]
    return [i for i in ids if not ((cv := latest(conn, i)) and cv["status"] == "done" and not is_stale(cv, stamp))]


def todo(conn) -> list[dict]:
    """What Claude needs to write each CV: the job message the writer and reviewer prompts expect."""
    out = []
    for job_id in todo_ids(conn):
        job, notes = _job(conn, job_id)
        out.append({"job_id": job_id, "file": tailor.filename(job), "message": tailor.job_message(job, notes)})
    return out


def _job(conn, job_id: int) -> tuple[dict, dict | None]:
    j = conn.execute("SELECT j.title, j.locations, j.description, c.name AS company, m.result FROM jobs j "
                     "JOIN companies c ON c.id = j.company_id LEFT JOIN match_evaluations m ON m.job_id = j.id "
                     "WHERE j.id = ?", (job_id,)).fetchone()
    job = {"title": j["title"], "company": j["company"], "locations": json.loads(j["locations"]),
           "description": j["description"] or ""}
    return job, json.loads(j["result"]) if j["result"] else None


def save_pdf(conn, job_id: int):
    """The job's finished CV as a PDF in the CV folder; None when its latest CV isn't finished."""
    job, _ = _job(conn, job_id)
    v = view(conn, {**job, "id": job_id})
    return pdf.save(v) if v["cv"] and v["cv"]["status"] == "done" else None


def save(conn, data: dict) -> tuple[int | None, list[str]]:
    """Store a CV Claude wrote ({job_id, final, final_review, draft?, review?}) and save its PDF. A CV that breaks
    a code rule is refused with the reasons, so it can be fixed and saved again."""
    job, notes = _job(conn, data["job_id"])
    final = tailor.clean_cv(data["final"])
    if found := tailor.problems(final, tailor.job_message(job, notes)):
        return None, found
    final_review = tailor.clean_review(data["final_review"])
    draft = tailor.clean_cv(data["draft"]) if data.get("draft") else final
    review = tailor.clean_review(data["review"]) if data.get("review") else final_review
    stamp, now = tailor.stamps(), now_iso()
    rid = conn.execute(
        "INSERT INTO tailored_cvs (job_id, created_at, finished_at, status, model, prompt_version, sources_hash, "
        "draft, review, final, final_review, score, cost_usd) VALUES (?, ?, ?, 'done', ?, ?, ?, ?, ?, ?, ?, ?, 0)",
        (data["job_id"], now, now, *(stamp[k] for k in STAMP_KEYS),
         *(json.dumps(x, ensure_ascii=False) for x in (draft, review, final, final_review)),
         final_review["score"])).lastrowid
    conn.commit()
    try:
        save_pdf(conn, data["job_id"])
    except Exception:
        log.exception("PDF for tailored CV %d failed; Download PDF on the job retries", rid)
    return rid, []
