import json
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from datetime import datetime, timezone

from ..db import connect
from ..match import SHOWN
from ..match.runner import cost
from ..normalize import now_iso
from . import CONTACT, get_setting, pdf, sources, tailor

WORKERS = 4
# Tokens for one CV (writer, review, reviser, final screen, usually a repair and a second screen), measured on the
# first real CVs: the pack is ~26k tokens and cached after the first call; with thinking, each pass writes 5–10k tokens.
EST_HIT, EST_MISS, EST_OUT = 150000, 40000, 48000
log = logging.getLogger(__name__)
_pool = ThreadPoolExecutor(WORKERS, thread_name_prefix="cv")
_lock = threading.Lock()
_active: set[int] = set()


def estimate(when: datetime | None = None) -> float:
    return cost(tailor.MODEL, EST_HIT, EST_MISS, EST_OUT, when or datetime.now(timezone.utc))


def _row(r) -> dict:
    d = dict(r)
    for k in ("draft", "review", "final", "final_review"):
        d[k] = json.loads(d[k]) if d[k] else None
    return d


def latest(conn, job_id: int) -> dict | None:
    """The newest CV for a job. A running row with no live worker (server restart) becomes an error."""
    r = conn.execute("SELECT * FROM tailored_cvs WHERE job_id = ? ORDER BY id DESC LIMIT 1", (job_id,)).fetchone()
    if not r:
        return None
    with _lock:
        lost = r["status"] == "running" and r["id"] not in _active
    if lost:
        conn.execute("UPDATE tailored_cvs SET status = 'error', error = ?, finished_at = ? WHERE id = ?",
                     ("Interrupted when the app restarted. Press Tailor again.", now_iso(), r["id"]))
        conn.commit()
        return latest(conn, job_id)
    return _row(r)


def view(conn, job: dict) -> dict:
    """Everything the CV section and the print page need."""
    cv = latest(conn, job["id"])
    contact = get_setting(conn, CONTACT)
    out = {"cv": cv, "contact": contact, "cv_est": estimate(), "stale": False, "markdown": "", "links": []}
    if cv and cv["status"] == "done":
        stamp = tailor.stamps()
        out["links"] = sources.links(sources.PACK.read_text())
        out["stale"] = (cv["prompt_version"], cv["sources_hash"]) != (stamp["prompt_version"], stamp["sources_hash"])
        out["markdown"] = tailor.to_markdown(cv["final"], contact, out["links"])
        out["filename"] = tailor.filename(job)
        out["pdf"] = pdf.location(out)
    return out


def ready(conn) -> set[int]:
    return {r[0] for r in conn.execute("SELECT DISTINCT job_id FROM tailored_cvs WHERE status = 'done'")}


def running_count(conn) -> int:
    with _lock:
        ids = list(_active)
    return conn.execute(f"SELECT COUNT(*) FROM tailored_cvs WHERE status = 'running' AND id IN ({','.join('?' * len(ids))})",
                        ids).fetchone()[0] if ids else 0


def batch_todo(conn) -> list[int]:
    """Shortlisted jobs without a CV that is done or being written."""
    return [r[0] for r in conn.execute(
        f"SELECT m.job_id FROM match_evaluations m WHERE m.verdict IN ({', '.join('?' * len(SHOWN))}) "
        "AND NOT EXISTS (SELECT 1 FROM tailored_cvs t WHERE t.job_id = m.job_id AND t.status IN ('done', 'running')) "
        "ORDER BY m.priority DESC", SHOWN)]


def start(db_path, key: str, job_ids: list[int]) -> int:
    """Queue a CV for each job that isn't already being written; returns how many were queued."""
    stamp = tailor.stamps()
    queued = []
    with closing(connect(db_path)) as conn:
        for job_id in job_ids:
            cv = latest(conn, job_id)
            if cv and cv["status"] == "running":
                continue
            rid = conn.execute(
                "INSERT INTO tailored_cvs (job_id, created_at, status, stage, model, prompt_version, sources_hash) "
                "VALUES (?, ?, 'running', 'queued', ?, ?, ?)",
                (job_id, now_iso(), stamp["model"], stamp["prompt_version"], stamp["sources_hash"])).lastrowid
            queued.append((rid, job_id))
        conn.commit()
    with _lock:
        _active.update(rid for rid, _ in queued)
    for rid, job_id in queued:
        _pool.submit(_run, db_path, key, rid, job_id)
    return len(queued)


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


def _run(db_path, key: str, rid: int, job_id: int) -> None:
    with closing(connect(db_path)) as conn:
        def stage(s):
            conn.execute("UPDATE tailored_cvs SET stage = ? WHERE id = ?", (s, rid))
            conn.commit()

        out = None
        try:
            job, notes = _job(conn, job_id)
            out = tailor.tailor(key, job, notes, stage)
        except Exception as e:
            log.exception("tailored CV %d for job %d failed", rid, job_id)
            conn.execute("UPDATE tailored_cvs SET status = 'error', error = ?, finished_at = ? WHERE id = ?",
                         (f"{type(e).__name__}: {e}"[:300], now_iso(), rid))
            conn.commit()
        if out:
            now = datetime.now(timezone.utc)
            usd = sum(cost(tailor.MODEL, u.get("prompt_cache_hit_tokens", 0), u.get("prompt_cache_miss_tokens", 0),
                           u.get("completion_tokens", 0), now) for u in out["usage"])
            conn.execute(
                "UPDATE tailored_cvs SET status = 'done', stage = NULL, finished_at = ?, draft = ?, review = ?, "
                "final = ?, final_review = ?, score = ?, cost_usd = ? WHERE id = ?",
                (now_iso(), *(json.dumps(out[k], ensure_ascii=False) for k in ("draft", "review", "final", "final_review")),
                 out["final_review"]["score"], usd, rid))
            conn.commit()
            log.info("tailored CV %d for job %d done: score %d (draft %d), $%.3f, %d calls", rid, job_id,
                     out["final_review"]["score"], out["review"]["score"], usd, len(out["usage"]))
            try:
                save_pdf(conn, job_id)
            except Exception:
                log.exception("PDF for tailored CV %d failed; Download PDF on the job retries", rid)
    with _lock:
        _active.discard(rid)

