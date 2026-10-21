import json

from .config import MATCH_WINDOW_DAYS, SIMILARITY_THRESHOLD
from .models import Posting
from .normalize import (ago_iso, ats_key_from_url, company_key, is_remote, now_iso, regions_for, shingles,
                        similarity, title_key, url_key)


def resolve_company(conn, name: str | None, website: str | None = None, now: str | None = None) -> int:
    key = company_key(name)
    row = conn.execute("SELECT id, website FROM companies WHERE key = ?", (key,)).fetchone()
    if row:
        if website and not row["website"]:
            conn.execute("UPDATE companies SET website = ? WHERE id = ?", (website, row["id"]))
        return row["id"]
    cur = conn.execute("INSERT INTO companies (key, name, website, created_at) VALUES (?, ?, ?, ?)",
                       (key, (name or "Unknown").strip(), website, now or now_iso()))
    return cur.lastrowid


def ingest(conn, postings: list[Posting], now: str | None = None) -> dict:
    now = now or now_iso()
    new_jobs = sum(_ingest_one(conn, p, now) for p in postings)
    conn.commit()
    return {"fetched": len(postings), "new_jobs": new_jobs}


def _ingest_one(conn, p: Posting, now: str) -> bool:
    akey = p.ats_key or ats_key_from_url(p.url)
    ukey = url_key(p.url)
    seen = conn.execute("SELECT id, job_id FROM sightings WHERE source = ? AND source_job_id = ?",
                        (p.source, p.source_job_id)).fetchone()
    if seen:
        conn.execute("UPDATE sightings SET last_seen_at = ?, url = ?, url_key = ?, ats_key = COALESCE(?, ats_key) "
                     "WHERE id = ?", (now, p.url, ukey, akey, seen["id"]))
        _merge(conn, seen["job_id"], p, now)
        return False
    company_id = resolve_company(conn, p.company, p.company_website, now)
    tkey = title_key(p.title)
    job_id, match = _find_job(conn, company_id, tkey, akey, ukey, p, now)
    created = job_id is None
    if created:
        job_id, match = _create(conn, company_id, tkey, p, now), "exact"
    else:
        _merge(conn, job_id, p, now)
    conn.execute(
        "INSERT INTO sightings (job_id, source, kind, source_job_id, ats_key, url, url_key, location, match, "
        "first_seen_at, last_seen_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (job_id, p.source, p.source.split(":")[0], p.source_job_id, akey, p.url, ukey,
         "; ".join(x for x in p.locations if x) or None, match, now, now),
    )
    return created


def _find_job(conn, company_id, tkey, akey, ukey, p, now):
    if akey:
        row = conn.execute("SELECT job_id FROM sightings WHERE ats_key = ? LIMIT 1", (akey,)).fetchone()
        if row:
            return row["job_id"], "exact"
    cands = conn.execute(
        "SELECT id, description FROM jobs WHERE company_id = ? AND title_key = ? AND last_seen_at >= ? "
        "ORDER BY last_seen_at DESC, id DESC",
        (company_id, tkey, ago_iso(now, days=MATCH_WINDOW_DAYS)),
    ).fetchall()
    if not cands:
        return None, None
    if ukey:
        for c in cands:
            if conn.execute("SELECT 1 FROM sightings WHERE job_id = ? AND url_key = ?", (c["id"], ukey)).fetchone():
                return c["id"], "exact"
    mine = shingles(p.description)
    scored = [(similarity(mine, shingles(c["description"])), c["id"]) for c in cands if mine and c["description"]]
    best_sim, best_id = max(scored, default=(0.0, None))
    if best_sim >= SIMILARITY_THRESHOLD:
        return best_id, "exact"
    for c in cands:
        if not mine or not c["description"]:
            return c["id"], "probable"
    return None, None


def _create(conn, company_id, tkey, p, now) -> int:
    locs = _uniq(p.locations)
    cur = conn.execute(
        "INSERT INTO jobs (company_id, title, title_key, description, desc_from_ats, locations, regions, remote, "
        "salary, apply_url, posted_at, first_seen_at, last_seen_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (company_id, p.title.strip(), tkey, p.description, int(p.from_ats and bool(p.description)),
         json.dumps(locs, ensure_ascii=False), json.dumps(regions_for(locs)), int(bool(p.remote) or is_remote(locs)),
         p.salary, p.url, p.posted_at, now, now),
    )
    _index(conn, cur.lastrowid)
    return cur.lastrowid


def _merge(conn, job_id, p, now) -> None:
    j = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    locs = _uniq(json.loads(j["locations"]) + p.locations)
    desc, from_ats = j["description"], j["desc_from_ats"]
    upgrade = bool(p.description) and (not desc or (p.from_ats and not from_ats))
    if upgrade:
        desc, from_ats = p.description, int(p.from_ats)
    apply_url = p.url if (p.from_ats and p.url) else (j["apply_url"] or p.url)
    posted = min((d for d in (j["posted_at"], p.posted_at) if d), default=None)
    conn.execute(
        "UPDATE jobs SET description = ?, desc_from_ats = ?, locations = ?, regions = ?, remote = ?, "
        "salary = COALESCE(salary, ?), apply_url = ?, posted_at = ?, last_seen_at = ? WHERE id = ?",
        (desc, from_ats, json.dumps(locs, ensure_ascii=False), json.dumps(regions_for(locs)),
         int(bool(j["remote"]) or bool(p.remote) or is_remote(locs)), p.salary, apply_url, posted, now, job_id),
    )
    if upgrade:
        _index(conn, job_id)


def _index(conn, job_id: int) -> None:
    row = conn.execute("SELECT j.title, c.name, j.description FROM jobs j JOIN companies c ON c.id = j.company_id "
                       "WHERE j.id = ?", (job_id,)).fetchone()
    conn.execute("DELETE FROM jobs_fts WHERE rowid = ?", (job_id,))
    conn.execute("INSERT INTO jobs_fts (rowid, title, company, description) VALUES (?, ?, ?, ?)",
                 (job_id, row["title"], row["name"], row["description"] or ""))


def _uniq(items: list[str]) -> list[str]:
    seen, out = set(), []
    for x in items:
        x = (x or "").strip()
        if x and x.lower() not in seen:
            seen.add(x.lower())
            out.append(x)
    return out
