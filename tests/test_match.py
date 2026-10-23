import pytest

from jobradar.ingest import ingest
from jobradar.match import import_results, set_label
from jobradar.models import Posting


def _job(conn):
    ingest(conn, [Posting(source="jobstash", source_job_id="1", company="Acme", title="Product Manager")])
    return conn.execute("SELECT id FROM jobs").fetchone()[0]


def _row(job_id, **kw):
    return {"job_id": job_id, "verdict": "apply_now", "track": "product", "rec": 80, "hm": 70, "want": 90,
            "why": "fits", "risk": "none", "start_cv": "OneKey Web3 PM", **kw}


def test_import_computes_priority_and_skips_unknown_jobs(conn):
    job_id = _job(conn)
    assert import_results(conn, [_row(job_id), _row(999)], run="manual") == 1
    r = conn.execute("SELECT run, verdict, priority FROM match_evaluations").fetchone()
    assert tuple(r) == ("manual", "apply_now", 81)


def test_reimport_updates_scores_but_keeps_label(conn):
    job_id = _job(conn)
    import_results(conn, [_row(job_id)], run="manual")
    set_label(conn, job_id, "N", "too junior")
    import_results(conn, [_row(job_id, verdict="stretch", rec=40)], run="opus")
    r = conn.execute("SELECT run, verdict, rec, label, label_note, labelled_at FROM match_evaluations").fetchone()
    assert r["run"] == "opus" and r["verdict"] == "stretch" and r["rec"] == 40
    assert (r["label"], r["label_note"]) == ("N", "too junior") and r["labelled_at"]


def test_set_label_clears_and_validates(conn):
    job_id = _job(conn)
    import_results(conn, [_row(job_id)], run="manual")
    set_label(conn, job_id, "Y", "")
    set_label(conn, job_id, "", "")
    r = conn.execute("SELECT label, label_note, labelled_at FROM match_evaluations").fetchone()
    assert tuple(r) == (None, None, None)
    with pytest.raises(ValueError):
        set_label(conn, job_id, "maybe", "")
