import json
from dataclasses import dataclass, field

from ..classify import COUNTRIES, ROLES, SENIORITY
from ..config import INTERVALS, STALE_DAYS
from ..lang import NAMES
from ..normalize import ago_iso, now_iso

SOURCE_GROUPS = [
    ("ats", "Company ATS"), ("jobstash", "JobStash"), ("getro", "VC boards · Getro"),
    ("consider", "VC boards · Consider"), ("web3career", "web3.career"), ("cryptojobslist", "cryptojobslist"),
    ("cryptocurrencyjobs", "cryptocurrencyjobs.co"), ("web3vacancy", "web3vacancy"), ("cryptojobs", "crypto.jobs"),
    ("telegram", "Telegram"), ("rebase", "Rebase 中文"), ("eleduck", "电鸭"), ("mycareersfuture", "MyCareersFuture SG"),
    ("linkedin", "LinkedIn"), ("seek", "JobsDB / JobStreet"), ("remote3", "remote3"), ("remoteok", "Remote OK"),
    ("remotive", "Remotive"), ("himalayas", "Himalayas"), ("foresight", "Foresight News 中文"),
    ("learnblockchain", "登链社区"), ("104", "104 人力銀行 (TW)"), ("wanted", "Wanted (KR)"),
    ("rocketpunch", "Rocketpunch (KR)"), ("green", "Green (JP)"), ("habr", "Habr Career (RU)"), ("hh", "hh.ru (RU)"),
    ("djinni", "Djinni (UA)"), ("dou", "DOU (UA)"), ("justjoin", "Just Join IT (PL)"), ("nofluff", "No Fluff Jobs (PL)"),
    ("arbeitnow", "Arbeitnow (DE)"), ("berlinstartupjobs", "Berlin Startup Jobs"), ("cutshort", "Cutshort (IN)"),
    ("itviec", "ITviec (VN)"), ("bitflyer", "bitFlyer careers (JP)"),
    ("board-only", "Not on any company ATS"),
]
POSTED_DAYS = {"24h": 1, "3d": 3, "7d": 7, "30d": 30, "all": None}
ORDER = {
    "posted": "j.posted_at IS NULL, j.posted_at DESC, j.id DESC",
    "new": "j.first_seen_at DESC, j.id DESC",
    "company": "c.name COLLATE NOCASE, j.title",
}


@dataclass
class Filters:
    q: str = ""
    posted: str = "7d"
    region: str = ""
    remote: str = ""
    source: str = ""
    company: int | None = None
    stale: bool = False
    sort: str = "posted"
    lang: list[str] = field(default_factory=list)
    sector: str = "crypto"
    role: list[str] = field(default_factory=list)
    seniority: list[str] = field(default_factory=list)
    country: str = ""
    salary: bool = False
    exclude: str = ""

    @property
    def more_set(self) -> bool:
        return bool(self.salary or self.exclude or self.lang or self.source)


def _where(f: Filters, now: str):
    where, args = [], []
    if not f.stale:
        where.append("j.last_seen_at >= ?")
        args.append(ago_iso(now, days=STALE_DAYS))
    if days := POSTED_DAYS.get(f.posted):
        where.append("j.posted_at >= ?")
        args.append(ago_iso(now, days=days))
    terms = f.q.replace('"', " ").split()
    if long_terms := [t for t in terms if len(t) >= 3]:
        where.append("j.id IN (SELECT rowid FROM jobs_fts WHERE jobs_fts MATCH ?)")
        args.append(" ".join(f'"{t}"' for t in long_terms))
    for t in (t for t in terms if len(t) < 3):
        where.append("(j.title LIKE ? OR c.name LIKE ?)")
        args += [f"%{t}%", f"%{t}%"]
    for t in f.exclude.replace('"', " ").split():
        if len(t) >= 3:
            where.append("j.id NOT IN (SELECT rowid FROM jobs_fts WHERE jobs_fts MATCH ?)")
            args.append(f'"{t}"')
        else:
            where.append("j.title NOT LIKE ?")
            args.append(f"%{t}%")
    for col, values in (("j.lang", f.lang), ("j.role", f.role), ("j.seniority", f.seniority)):
        if values:
            where.append(f"{col} IN ({', '.join('?' * len(values))})")
            args += values
    if f.sector == "crypto":
        where.append("c.sector = 'crypto'")
    if f.country:
        where.append("EXISTS (SELECT 1 FROM json_each(j.countries) WHERE value = ?)")
        args.append(f.country)
    if f.salary:
        where.append("j.salary IS NOT NULL")
    if f.region:
        where.append("j.regions LIKE ?")
        args.append(f'%"{f.region}"%')
    if f.remote == "anywhere":
        where.append("j.remote_scope = 'anywhere'")
    elif f.remote:
        where.append("j.remote = 1")
    if f.company:
        where.append("j.company_id = ?")
        args.append(f.company)
    if f.source == "board-only":
        where.append("NOT EXISTS (SELECT 1 FROM sightings s WHERE s.job_id = j.id AND s.kind = 'ats')")
    elif f.source:
        where.append("EXISTS (SELECT 1 FROM sightings s WHERE s.job_id = j.id AND s.kind = ?)")
        args.append(f.source)
    return ("WHERE " + " AND ".join(where)) if where else "", args


def search_jobs(conn, f: Filters, limit: int = 50, offset: int = 0, now: str | None = None):
    now = now or now_iso()
    where, args = _where(f, now)
    base = f"FROM jobs j JOIN companies c ON c.id = j.company_id {where}"
    total = conn.execute(f"SELECT COUNT(*) {base}", args).fetchone()[0]
    rows = conn.execute(
        f"SELECT j.id, j.title, j.locations, j.remote, j.salary, j.posted_at, j.first_seen_at, j.lang, "
        f"c.name AS company, "
        f"(SELECT COUNT(*) FROM sightings s WHERE s.job_id = j.id) AS n_sources, "
        f"(SELECT group_concat(DISTINCT s.kind) FROM sightings s WHERE s.job_id = j.id) AS kinds "
        f"{base} ORDER BY {ORDER.get(f.sort, ORDER['posted'])} LIMIT ? OFFSET ?",
        [*args, limit, offset],
    ).fetchall()
    day_ago = ago_iso(now, days=1)
    jobs = [{**dict(r), "locations": json.loads(r["locations"]), "kinds": sorted((r["kinds"] or "").split(",")),
             "is_new": r["first_seen_at"] >= day_ago} for r in rows]
    return jobs, total


def facets(conn, sector: str = "crypto", now: str | None = None) -> dict[str, list[tuple[str, str, int]]]:
    base = ("FROM jobs j JOIN companies c ON c.id = j.company_id WHERE j.last_seen_at >= ?"
            + (" AND c.sector = 'crypto'" if sector == "crypto" else ""))
    cutoff = (ago_iso(now or now_iso(), days=STALE_DAYS),)

    def count(col, names, order_by_name=False):
        rows = conn.execute(f"SELECT {col}, COUNT(*) {base} AND {col} IS NOT NULL GROUP BY 1 ORDER BY 2 DESC", cutoff)
        out = [(k, names.get(k, k), n) for k, n in rows]
        return sorted(out, key=lambda r: list(names).index(r[0]) if r[0] in names else 99) if order_by_name else out

    countries = conn.execute(f"SELECT value, COUNT(*) FROM jobs j JOIN companies c ON c.id = j.company_id, "
                             f"json_each(j.countries) {base[base.index('WHERE'):]} GROUP BY 1 ORDER BY 2 DESC "
                             f"LIMIT 40", cutoff)
    return {"lang": count("j.lang", NAMES), "role": count("j.role", ROLES, True),
            "seniority": count("j.seniority", SENIORITY, True),
            "country": sorted(((k, COUNTRIES[k][0], n) for k, n in countries if k in COUNTRIES), key=lambda r: r[1])}


def job_detail(conn, job_id: int):
    j = conn.execute("SELECT j.*, c.name AS company, c.website FROM jobs j JOIN companies c ON c.id = j.company_id "
                     "WHERE j.id = ?", (job_id,)).fetchone()
    if not j:
        return None, []
    sightings = conn.execute("SELECT * FROM sightings WHERE job_id = ? ORDER BY kind != 'ats', first_seen_at",
                             (job_id,)).fetchall()
    return {**dict(j), "locations": json.loads(j["locations"])}, [dict(s) for s in sightings]


def companies(conn, q: str = "", now: str | None = None) -> list[dict]:
    cutoff = ago_iso(now or now_iso(), days=STALE_DAYS)
    rows = conn.execute(
        "SELECT c.id, c.name, c.website, c.sector, c.sector_source, "
        "(SELECT COUNT(*) FROM jobs j WHERE j.company_id = c.id AND j.last_seen_at >= ?) AS active, "
        "(SELECT group_concat(b.ats || ':' || b.slug, '  ') FROM boards b WHERE b.company_id = c.id) AS boards "
        "FROM companies c WHERE c.name LIKE ? ORDER BY active DESC, c.name COLLATE NOCASE LIMIT 1000",
        (cutoff, f"%{q}%"),
    )
    return [dict(r) for r in rows]


def sources_status(conn, sources: list[str]) -> list[dict]:
    counts = dict(conn.execute("SELECT kind, COUNT(DISTINCT job_id) FROM sightings GROUP BY kind").fetchall())
    out = []
    for name in sources:
        r = conn.execute("SELECT * FROM source_runs WHERE source = ? ORDER BY id DESC LIMIT 1", (name,)).fetchone()
        out.append({"name": name, "interval": INTERVALS.get(name), "jobs": counts.get(name, 0),
                    **(dict(r) if r else {"status": "never"})})
    return out


def boards_summary(conn):
    by_ats = conn.execute(
        "SELECT ats, COUNT(*) AS boards, SUM(enabled) AS enabled, SUM(last_status LIKE 'error%') AS errors, "
        "SUM(COALESCE(last_count, 0)) AS jobs FROM boards GROUP BY ats ORDER BY boards DESC").fetchall()
    failing = conn.execute(
        "SELECT c.name, b.ats, b.slug, b.last_status FROM boards b JOIN companies c ON c.id = b.company_id "
        "WHERE b.last_status LIKE 'error%' ORDER BY c.name LIMIT 200").fetchall()
    return [dict(r) for r in by_ats], [dict(r) for r in failing]


def header_stats(conn, now: str | None = None) -> dict:
    now = now or now_iso()
    cutoff = ago_iso(now, days=STALE_DAYS)

    def one(sql, *args):
        return conn.execute(sql, args).fetchone()[0]

    return {
        "active": one("SELECT COUNT(*) FROM jobs WHERE last_seen_at >= ?", cutoff),
        "new_24h": one("SELECT COUNT(*) FROM jobs WHERE first_seen_at >= ?", ago_iso(now, days=1)),
        "companies": one("SELECT COUNT(DISTINCT company_id) FROM jobs WHERE last_seen_at >= ?", cutoff),
        "source_errors": one("SELECT COUNT(*) FROM source_runs WHERE id IN "
                             "(SELECT MAX(id) FROM source_runs GROUP BY source) AND status = 'error'"),
        "last_poll": one("SELECT MAX(finished_at) FROM source_runs"),
    }
