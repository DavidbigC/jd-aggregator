from .. import enrich, prefs as preferences
from ..http import Http
from ..ingest import apply_detail
from ..normalize import now_iso
from . import evaluate, import_results, prefilter

JOB_KEYS = ("id", "title", "company", "locations", "place", "salary", "posted_at", "description")


def needs_scoring(row, job: dict, stamp: dict) -> bool:
    if row is None or row["model"] is None:
        return True
    return (row["description_hash"] != evaluate.digest(job["description"] or "")
            or any(row[k] != stamp[k] for k in ("model", "prompt_version", "profile_hash", "prefs_version")))


def plan(conn, now: str | None = None) -> dict:
    """Prefilter, then which jobs are new or changed since they were last scored."""
    now = now or now_iso()
    p, version = preferences.current(conn)
    jobs, steps = prefilter.run(conn, p, now)
    stamp = evaluate.stamps(version)
    rows = {r["job_id"]: r for r in conn.execute("SELECT * FROM match_evaluations")}
    todo = [j for j in jobs if needs_scoring(rows.get(j["id"]), j, stamp)]
    # Labelled and hand-scored jobs first, so they double as a calibration set.
    todo.sort(key=lambda j: (rows.get(j["id"]) is None or rows[j["id"]]["label"] is None,
                             rows.get(j["id"]) is None, j["place"] != "remote anywhere", -j["id"]))
    return {"prefs": p, "prefs_version": version, "stamp": stamp, "steps": steps, "todo": todo,
            "model": evaluate.MODEL}


def last_run(conn) -> dict | None:
    row = conn.execute("SELECT * FROM match_runs ORDER BY id DESC LIMIT 1").fetchone()
    return dict(row) if row else None


def todo(conn, http: Http | None = None) -> dict:
    """The jobs Claude should score, with the preferences. A thin ad gets one fetch of the full ad; if it is still
    too short to judge, it is saved as needs_ad and left out."""
    p = plan(conn)
    http = http or Http()
    jobs, thin = [], 0
    for job in p["todo"]:
        if len(job["description"] or "") < prefilter.MIN_AD:
            urls = [r[0] for r in conn.execute("SELECT detail_url FROM sightings WHERE job_id = ? ORDER BY kind != 'ats'",
                                               (job["id"],))] + [job["apply_url"]]
            urls = list(dict.fromkeys(u for u in urls if u))[:3]
            detail, _ = enrich._fetch(http, job["title"], urls) if urls else (None, "no-url")
            if detail and len(detail.description or "") > len(job["description"] or ""):
                apply_detail(conn, job["id"], detail, now_iso(), "match-fetch")
                job = {**job, "description": detail.description}
        if len(job["description"] or "") < prefilter.MIN_AD:
            thin += 1
            import_results(conn, [{"job_id": job["id"], "verdict": "needs_ad", "track": None, "why": None,
                                   "risk": "The ad is too short to judge. Open it and check the employer's page.",
                                   "description_hash": evaluate.digest(job["description"] or ""), **p["stamp"]}],
                           run="needs-ad")
            continue
        jobs.append({k: job[k] for k in JOB_KEYS})
    return {"prefs": p["prefs"], "jobs": jobs, "needs_ad": thin}


def save_results(conn, answers: list[dict]) -> tuple[int, list[str]]:
    """Claude's matcher answers ({"job_id", ...the match_prompt shape}): checked, given verdicts by the code rules,
    and upserted with labels kept. Returns how many were saved and what was refused."""
    _, version = preferences.current(conn)
    stamp = evaluate.stamps(version)
    rows, refused = [], []
    for a in answers:
        job = conn.execute("SELECT description FROM jobs WHERE id = ?", (a.get("job_id"),)).fetchone()
        if not job:
            refused.append(f"job {a.get('job_id')}: no such job")
            continue
        try:
            rows.append(evaluate.row(a["job_id"], job["description"] or "", a, stamp))
        except ValueError as e:
            refused.append(f"job {a['job_id']}: {e}")
    now = now_iso()
    run_id = conn.execute(
        "INSERT INTO match_runs (started_at, finished_at, status, model, prefs_version, planned, evaluated, failed) "
        "VALUES (?, ?, 'done', ?, ?, ?, ?, ?)",
        (now, now, evaluate.MODEL, version, len(answers), len(rows), len(refused))).lastrowid
    conn.commit()
    import_results(conn, rows, run=f"claude-{run_id}")
    return len(rows), refused
