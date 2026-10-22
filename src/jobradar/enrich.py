from concurrent.futures import ThreadPoolExecutor, as_completed

from . import detail
from .config import ENRICH_BATCH, ENRICH_RETRY_DAYS, STALE_DAYS
from .ingest import apply_detail
from .normalize import ago_iso, title_key

WORKERS = 8
THIN = 200


def candidates(conn, now: str, limit: int) -> list[tuple[int, str, list[str]]]:
    jobs = conn.execute(
        "SELECT id, title, apply_url FROM jobs WHERE last_seen_at >= ? "
        "AND (description IS NULL OR length(description) < ? OR posted_at IS NULL) "
        "AND (enriched_at IS NULL OR enriched_at < ?) ORDER BY first_seen_at DESC, id DESC LIMIT ?",
        (ago_iso(now, days=STALE_DAYS), THIN, ago_iso(now, days=ENRICH_RETRY_DAYS), limit),
    ).fetchall()
    out = []
    for j in jobs:
        s = conn.execute("SELECT detail_url, url FROM sightings WHERE job_id = ? ORDER BY kind != 'ats', id",
                         (j["id"],)).fetchall()
        urls = [r["detail_url"] for r in s] + [j["apply_url"]] + [r["url"] for r in s]
        out.append((j["id"], j["title"], list(dict.fromkeys(u for u in urls if u))[:3]))
    return out


def _same_job(title: str, d: detail.Detail) -> bool:
    want = set(title_key(title).split())
    got = set(title_key(f"{d.title or ''} {(d.description or '')[:300]}").split())
    return not want or len(want & got) * 2 >= len(want)


def _fetch(http, title: str, urls: list[str]) -> tuple[detail.Detail | None, str]:
    status = "no-url"
    for url in urls:
        try:
            d = detail.parse(http.html(url))
        except Exception as e:
            status = f"error: {e!r}"[:200]
            continue
        if not _same_job(title, d):
            status = "other-page"
        elif (d.description and len(d.description) >= THIN) or d.posted_at:
            return d, "ok"
        else:
            status = "thin"
    return None, status


def run(conn, http, now: str, limit: int = ENRICH_BATCH) -> dict:
    jobs = candidates(conn, now, limit)
    improved = 0
    with ThreadPoolExecutor(WORKERS) as pool:
        futures = {pool.submit(_fetch, http, title, urls): job_id for job_id, title, urls in jobs}
        for fut in as_completed(futures):
            d, status = fut.result()
            improved += apply_detail(conn, futures[fut], d, now, status)
            conn.commit()
    return {"fetched": len(jobs), "new_jobs": improved}
