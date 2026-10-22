import fcntl
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from itertools import chain

from . import enrich
from .collectors import AGGREGATORS, sites
from .collectors.ats import ADAPTERS
from .config import DATA_DIR, INTERVALS
from .http import Http
from .ingest import ingest
from .normalize import ago_iso, is_web3, now_iso
from .registry import discover_boards

SOURCES = ["ats", *AGGREGATORS, *sites.SITES, "enrich"]
ATS_WORKERS = 8


def due_sources(conn, now: str, force: bool = False, only: list[str] | None = None) -> list[str]:
    names = list(only or SOURCES)
    if force:
        return names
    due = []
    for name in names:
        last = conn.execute("SELECT MAX(started_at) FROM source_runs WHERE source = ?", (name,)).fetchone()[0]
        if not last or last <= ago_iso(now, minutes=INTERVALS.get(name, 60)):
            due.append(name)
    return due


def _fetcher(conn, name: str):
    if name in sites.SITES:
        seen = {r[0] for r in conn.execute("SELECT source_job_id FROM sightings WHERE source = ?", (name,))}
        skipped = {r[0] for r in conn.execute("SELECT source_job_id FROM skipped WHERE source = ?", (name,))}
        return lambda http: sites.collect(http, name, seen, skipped)
    return AGGREGATORS[name]


def _fetch_board(http, b) -> tuple[list, str]:
    try:
        return ADAPTERS[b["ats"]](http, b["slug"], b["name"]), "ok"
    except Exception as e:
        return [], f"error: {e!r}"[:300]


def _run_ats(conn, http, now: str) -> dict:
    boards = conn.execute("SELECT b.id, b.ats, b.slug, b.crypto_only, b.last_polled_at, b.last_status, c.name "
                          "FROM boards b JOIN companies c ON c.id = b.company_id WHERE b.enabled = 1 ORDER BY b.id"
                          ).fetchall()
    stats = {"fetched": 0, "new_jobs": 0}
    with ThreadPoolExecutor(ATS_WORKERS) as pool:
        futures = {pool.submit(_fetch_board, http, b): b for b in boards}
        for fut in as_completed(futures):
            postings, status = fut.result()
            b = futures[fut]
            if b["crypto_only"]:
                postings = [p for p in postings if is_web3(p.title)]
            conn.execute("UPDATE boards SET last_polled_at = ?, last_status = ?, last_count = ? WHERE id = ?",
                         (now, status, len(postings), b["id"]))
            polled_before = bool(b["last_polled_at"]) and (b["last_status"] or "").startswith("ok")
            s = ingest(conn, postings, now, trust_new=polled_before)
            stats = {k: stats[k] + s[k] for k in stats}
    return stats


def run_source(conn, http, name: str, now: str | None = None, fetched: Future | None = None) -> dict:
    now = now or now_iso()
    polled_before = bool(conn.execute("SELECT 1 FROM source_runs WHERE source = ? AND status = 'ok' LIMIT 1",
                                      (name,)).fetchone())
    run_id = conn.execute("INSERT INTO source_runs (source, started_at, status) VALUES (?, ?, 'running')",
                          (name, now)).lastrowid
    conn.commit()
    try:
        if name == "ats":
            stats = _run_ats(conn, http, now)
        elif name == "enrich":
            stats = enrich.run(conn, http, now)
        else:
            got = fetched.result() if fetched else _fetcher(conn, name)(http)
            postings, skipped = got if isinstance(got, tuple) else (got, [])
            conn.executemany("INSERT OR IGNORE INTO skipped (source, source_job_id, at) VALUES (?, ?, ?)",
                             [(name, s, now) for s in skipped])
            stats = ingest(conn, postings, now, trust_new=polled_before)
            discover_boards(conn, postings)
        result = {"status": "ok", "fetched": stats["fetched"], "new_jobs": stats["new_jobs"], "error": None}
    except Exception as e:
        conn.rollback()
        result = {"status": "error", "fetched": 0, "new_jobs": 0, "error": repr(e)[:500]}
    conn.execute("UPDATE source_runs SET finished_at = ?, status = ?, fetched = ?, new_jobs = ?, error = ? WHERE id = ?",
                 (now_iso(), result["status"], result["fetched"], result["new_jobs"], result["error"], run_id))
    conn.commit()
    return result


@contextmanager
def poll_lock():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DATA_DIR / "poll.lock", "w") as fh:
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            yield False
            return
        yield True


def poll(conn, sources: list[str] | None = None, force: bool = False, http=None, log=print) -> list:
    with poll_lock() as acquired:
        if not acquired:
            log("another poll is running; skipping")
            return []
        own_http, http = http is None, http or Http()
        due = due_sources(conn, now_iso(), force=force, only=sources)
        fetched = [n for n in due if n not in ("ats", "enrich")]
        results = []
        try:
            with ThreadPoolExecutor(max(1, len(fetched))) as pool:
                fetches = {pool.submit(_fetcher(conn, n), http): n for n in fetched}
                steps = chain([("ats", None)] * ("ats" in due), ((fetches[f], f) for f in as_completed(fetches)),
                              [("enrich", None)] * ("enrich" in due))
                for name, fut in steps:
                    r = run_source(conn, http, name, fetched=fut)
                    log(f"{name:20s} {r['status']:5s} fetched={r['fetched']:<6} new={r['new_jobs']:<5} "
                        f"{r['error'] or ''}")
                    results.append((name, r))
        finally:
            if own_http:
                http.close()
        return results
