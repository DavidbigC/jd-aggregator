import fcntl
from contextlib import contextmanager

from .collectors import AGGREGATORS
from .collectors.ats import ADAPTERS
from .config import DATA_DIR, INTERVALS
from .http import Http
from .ingest import ingest
from .normalize import ago_iso, now_iso
from .registry import discover_boards

SOURCES = ["ats", *AGGREGATORS]


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


def _collect_ats(conn, http, now: str) -> list:
    boards = conn.execute("SELECT b.id, b.ats, b.slug, c.name FROM boards b JOIN companies c ON c.id = b.company_id "
                          "WHERE b.enabled = 1 ORDER BY b.id").fetchall()
    out = []
    for b in boards:
        try:
            postings, status = ADAPTERS[b["ats"]](http, b["slug"], b["name"]), "ok"
        except Exception as e:
            postings, status = [], f"error: {e!r}"[:300]
        conn.execute("UPDATE boards SET last_polled_at = ?, last_status = ?, last_count = ? WHERE id = ?",
                     (now, status, len(postings), b["id"]))
        out += postings
    conn.commit()
    return out


def run_source(conn, http, name: str, now: str | None = None) -> dict:
    now = now or now_iso()
    run_id = conn.execute("INSERT INTO source_runs (source, started_at, status) VALUES (?, ?, 'running')",
                          (name, now)).lastrowid
    conn.commit()
    try:
        postings = _collect_ats(conn, http, now) if name == "ats" else AGGREGATORS[name](http)
        stats = ingest(conn, postings, now)
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
        http = http or Http()
        results = []
        for name in due_sources(conn, now_iso(), force=force, only=sources):
            r = run_source(conn, http, name)
            log(f"{name:20s} {r['status']:5s} fetched={r['fetched']:<6} new={r['new_jobs']:<5} {r['error'] or ''}")
            results.append((name, r))
        return results
