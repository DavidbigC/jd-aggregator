from ..normalize import now_iso

VERDICTS = {"apply_now": "Apply now", "tailor_then_apply": "Tailor then apply", "stretch": "Stretch",
            "needs_ad": "Ad too short to judge", "skip": "Skipped"}
SHOWN = ("apply_now", "tailor_then_apply", "stretch")
LABELS = {"Y", "M", "N"}
FIELDS = ("verdict", "track", "rec", "hm", "want", "why", "risk", "start_cv", "reason", "model", "prompt_version",
          "profile_hash", "prefs_version", "description_hash", "result")


def priority(rec: int, hm: int, want: int) -> int:
    """Weighted geometric mean, 0–100: Want counts most, Rec least, because the tailored CV is how Rec gets lifted."""
    return round(rec ** 0.15 * hm ** 0.35 * want ** 0.5)


def import_results(conn, rows: list[dict], run: str) -> int:
    """Upsert evaluations; David's label fields are never touched."""
    known = {r[0] for r in conn.execute("SELECT id FROM jobs")}
    now, n = now_iso(), 0
    for r in rows:
        if r["job_id"] not in known:
            continue
        conn.execute(
            f"INSERT INTO match_evaluations (job_id, run, priority, created_at, {', '.join(FIELDS)}) "
            f"VALUES (?, ?, ?, ?, {', '.join('?' * len(FIELDS))}) "
            f"ON CONFLICT (job_id) DO UPDATE SET run = excluded.run, priority = excluded.priority, "
            f"created_at = excluded.created_at, {', '.join(f'{c} = excluded.{c}' for c in FIELDS)}",
            (r["job_id"], run, priority(r["rec"], r["hm"], r["want"]) if r.get("rec") is not None else None, now,
             *(r.get(c) for c in FIELDS)),
        )
        n += 1
    conn.commit()
    return n


def set_label(conn, job_id: int, label: str, note: str) -> None:
    if label and label not in LABELS:
        raise ValueError(label)
    conn.execute("UPDATE match_evaluations SET label = ?, label_note = ?, labelled_at = ? WHERE job_id = ?",
                 (label or None, note.strip() or None if label else None, now_iso() if label else None, job_id))
    conn.commit()
