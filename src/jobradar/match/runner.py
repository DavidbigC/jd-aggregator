import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import closing
from datetime import datetime, timezone

import httpx

from .. import enrich, prefs as preferences
from ..db import connect
from ..http import Http
from ..ingest import apply_detail
from ..normalize import ISO, now_iso
from . import evaluate, import_results, prefilter

WORKERS = 8
SAMPLE = 20
# USD per 1M tokens at peak: cache hit, cache miss, output. Off-peak is half.
PRICES = {"deepseek-v4-pro": (0.044, 1.32, 3.96), "deepseek-flash": (0.006, 0.30, 1.20)}
# Measured on the first live calls: ~5.3k prompt tokens (profile + prompt + preferences + a ~5k-character ad)
# and ~3.7k output tokens, most of it thinking.
EST_PROMPT, EST_OUTPUT = 4000, 3800
log = logging.getLogger(__name__)
_lock = threading.Lock()
_thread: threading.Thread | None = None


class AlreadyRunning(Exception):
    pass


def is_peak(when: datetime) -> bool:
    return when.weekday() < 5 and (1 <= when.hour < 4 or 6 <= when.hour < 10)


def cost(model: str, hit: int, miss: int, out: int, when: datetime) -> float:
    p_hit, p_miss, p_out = PRICES[model]
    return (hit * p_hit + miss * p_miss + out * p_out) / 1e6 * (1 if is_peak(when) else 0.5)


def needs_scoring(row, job: dict, stamp: dict) -> bool:
    if row is None or row["model"] is None:
        return True
    return (row["description_hash"] != evaluate.digest(job["description"] or "")
            or any(row[k] != stamp[k] for k in ("model", "prompt_version", "profile_hash", "prefs_version")))


def plan(conn, now: str | None = None) -> dict:
    """The free part: prefilter, then which jobs are new or changed since they were last scored."""
    now = now or now_iso()
    p, version = preferences.current(conn)
    jobs, steps = prefilter.run(conn, p, now)
    stamp = evaluate.stamps(version)
    rows = {r["job_id"]: r for r in conn.execute("SELECT * FROM match_evaluations")}
    todo = [j for j in jobs if needs_scoring(rows.get(j["id"]), j, stamp)]
    # Labelled and hand-scored jobs first, so "Try 20 first" doubles as a calibration set.
    todo.sort(key=lambda j: (rows.get(j["id"]) is None or rows[j["id"]]["label"] is None,
                             rows.get(j["id"]) is None, j["place"] != "remote anywhere", -j["id"]))
    when = datetime.strptime(now, ISO).replace(tzinfo=timezone.utc)
    per_job = cost(evaluate.MODEL, 0, EST_PROMPT, EST_OUTPUT, when)
    return {"prefs": p, "prefs_version": version, "stamp": stamp, "steps": steps, "todo": todo,
            "thin": sum(len(j["description"] or "") < prefilter.MIN_AD for j in todo), "per_job": per_job,
            "peak": is_peak(when), "model": evaluate.MODEL}


def running(conn) -> dict | None:
    with _lock:
        alive = bool(_thread and _thread.is_alive())
        row = conn.execute("SELECT * FROM match_runs WHERE status = 'running' ORDER BY id DESC LIMIT 1").fetchone()
    if row and not alive:
        conn.execute("UPDATE match_runs SET status = 'interrupted', finished_at = ? WHERE status = 'running'",
                     (now_iso(),))
        conn.commit()
        return None
    return dict(row) if row else None


def last_run(conn) -> dict | None:
    row = conn.execute("SELECT * FROM match_runs ORDER BY id DESC LIMIT 1").fetchone()
    return dict(row) if row else None


def start(db_path, key: str, limit: int | None = None) -> int:
    """Start a background run; raise AlreadyRunning if one is in progress in this process."""
    global _thread
    with _lock:
        if _thread and _thread.is_alive():
            raise AlreadyRunning
        with closing(connect(db_path)) as conn:
            conn.execute("UPDATE match_runs SET status = 'interrupted', finished_at = ? WHERE status = 'running'",
                         (now_iso(),))
            p = plan(conn)
            todo = p["todo"][:limit] if limit else p["todo"]
            run_id = conn.execute(
                "INSERT INTO match_runs (started_at, status, model, prefs_version, planned) VALUES (?, 'running', ?, ?, ?)",
                (now_iso(), p["model"], p["prefs_version"], len(todo))).lastrowid
            conn.commit()
        _thread = threading.Thread(target=_run, args=(db_path, key, run_id, p, todo), daemon=True)
        _thread.start()
        return run_id


def _score(http, key: str, job: dict, p: dict):
    detail = None
    if len(job["description"] or "") < prefilter.MIN_AD:
        detail, _ = enrich._fetch(http, job["title"], job["urls"]) if job["urls"] else (None, "no-url")
        if detail and len(detail.description or "") > len(job["description"] or ""):
            job = {**job, "description": detail.description}
    if len(job["description"] or "") < prefilter.MIN_AD:
        return detail, {"job_id": job["id"], "verdict": "needs_ad", "track": None, "why": None,
                        "risk": "The ad is too short to judge. Open it and check the employer's page.",
                        "description_hash": evaluate.digest(job["description"] or ""), **p["stamp"]}, {}
    row, usage = evaluate.evaluate(key, job, p["prefs"], p["stamp"])
    return detail, row, usage


def _run(db_path, key: str, run_id: int, p: dict, todo: list[dict]) -> None:
    error = None
    http = Http()
    with closing(connect(db_path)) as conn, ThreadPoolExecutor(WORKERS) as pool:
        for job in todo:
            urls = [r[0] for r in conn.execute("SELECT detail_url FROM sightings WHERE job_id = ? ORDER BY kind != 'ats'",
                                               (job["id"],))] + [job["apply_url"]]
            job["urls"] = list(dict.fromkeys(u for u in urls if u))[:3]
        futures = {pool.submit(_score, http, key, job, p): job for job in todo}
        for fut in as_completed(futures):
            job = futures[fut]
            try:
                detail, row, usage = fut.result()
            except httpx.HTTPStatusError as e:
                log.exception("match run %d: job %d failed", run_id, job["id"])
                conn.execute("UPDATE match_runs SET failed = failed + 1 WHERE id = ?", (run_id,))
                conn.commit()
                if e.response.status_code in (401, 402):
                    error = f"DeepSeek refused the key ({e.response.status_code}). Check Settings."
                    for f in futures:
                        f.cancel()
                    break
                continue
            except Exception:
                log.exception("match run %d: job %d failed", run_id, job["id"])
                conn.execute("UPDATE match_runs SET failed = failed + 1 WHERE id = ?", (run_id,))
                conn.commit()
                continue
            if detail:
                apply_detail(conn, job["id"], detail, now_iso(), "match-fetch")
            import_results(conn, [row], run=f"deepseek-{run_id}")
            hit, miss = usage.get("prompt_cache_hit_tokens", 0), usage.get("prompt_cache_miss_tokens", 0)
            out = usage.get("completion_tokens", 0)
            conn.execute(
                "UPDATE match_runs SET evaluated = evaluated + 1, input_hit = input_hit + ?, input_miss = input_miss + ?, "
                "output_tokens = output_tokens + ?, cost_usd = cost_usd + ? WHERE id = ?",
                (hit, miss, out, cost(p["model"], hit, miss, out, datetime.now(timezone.utc)), run_id))
            conn.commit()
        conn.execute("UPDATE match_runs SET status = ?, finished_at = ?, error = ? WHERE id = ?",
                     ("error" if error else "done", now_iso(), error, run_id))
        conn.commit()
    http.close()
    log.info("match run %d finished%s", run_id, f": {error}" if error else "")
