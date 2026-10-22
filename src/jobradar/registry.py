import csv

from .config import SUPPORTED_ATS
from .ingest import resolve_company
from .models import Posting
from .normalize import ats_board_from_url


def load_seed(conn, path) -> int:
    added = 0
    with open(path, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            cid = resolve_company(conn, r["company"], r["website"] or None)
            enabled = int(r["enabled"] == "1" and r["ats"] in SUPPORTED_ATS)
            crypto_only = int(r.get("crypto_only") == "1")
            added += conn.execute("INSERT OR IGNORE INTO boards (company_id, ats, slug, origin, enabled, crypto_only) "
                                  "VALUES (?, ?, ?, ?, ?, ?)",
                                  (cid, r["ats"], r["slug"], r["origin"], enabled, crypto_only)).rowcount
            conn.execute("UPDATE boards SET crypto_only = ? WHERE ats = ? AND slug = ?",
                         (crypto_only, r["ats"], r["slug"]))
    conn.commit()
    return added


def discover_boards(conn, postings: list[Posting]) -> int:
    added = 0
    for p in postings:
        found = ats_board_from_url(p.url)
        if not found or found[0] not in SUPPORTED_ATS:
            continue
        if conn.execute("SELECT 1 FROM boards WHERE ats = ? AND lower(slug) = lower(?)", found).fetchone():
            continue
        cid = resolve_company(conn, p.company, p.company_website)
        added += conn.execute("INSERT OR IGNORE INTO boards (company_id, ats, slug, origin, enabled) "
                              "VALUES (?, ?, ?, 'discovered', 1)", (cid, *found)).rowcount
    conn.commit()
    return added
