import argparse
import json
from pathlib import Path

from . import prefs
from .classify import company_sectors, reclassify_jobs
from .config import CV_PDF_DIR, CV_SOURCE_DIR, DB_PATH, SECTORS_CSV, SEED_CSV
from .cv import runner as cvs
from .cv import sources
from .db import connect
from .lang import detect_lang
from .match import import_results
from .match import runner as matcher
from .match.evaluate import rescore
from .registry import load_sectors, load_seed
from .runner import poll


def main() -> None:
    ap = argparse.ArgumentParser(prog="jd_aggregator")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("seed", help="load seeds/boards.csv into the board registry")
    p = sub.add_parser("poll", help="run every source that is due")
    p.add_argument("--source", action="append", help="limit to this source (repeatable)")
    p.add_argument("--force", action="store_true", help="ignore intervals")
    sub.add_parser("relang", help="detect the language of every job")
    sub.add_parser("reclassify", help="recompute job roles, seniority, countries and company sectors")
    m = sub.add_parser("match", help="job-fit evaluations shown on /shortlist")
    msub = m.add_subparsers(dest="match_cmd", required=True)
    mi = msub.add_parser("import", help="load evaluations from a JSON file (labels are kept)")
    mi.add_argument("path")
    mi.add_argument("--run", help="run name (default: the file name)")
    msub.add_parser("rescore", help="re-derive verdicts and priorities from stored scores")
    mt = msub.add_parser("todo", help="write the jobs Claude should score, with the preferences, to a JSON file")
    mt.add_argument("path")
    mr = msub.add_parser("results", help="load Claude's matcher answers; the code applies the verdict rules")
    mr.add_argument("path")
    c = sub.add_parser("cv", help="tailored CVs")
    csub = c.add_subparsers(dest="cv_cmd", required=True)
    cs = csub.add_parser("sources", help="rebuild seeds/cv_sources.md from devmaster-cv, scrubbed")
    cs.add_argument("--src", default=str(CV_SOURCE_DIR))
    csub.add_parser("pdfs", help=f"save every finished CV as a PDF in {CV_PDF_DIR}")
    ct = csub.add_parser("todo", help="write the shortlisted jobs that need a new CV to a JSON file")
    ct.add_argument("path")
    cv_save = csub.add_parser("save", help="store CVs Claude wrote (one object or a list) after the code checks")
    cv_save.add_argument("path")
    pr = sub.add_parser("prefs", help="job preferences")
    psub = pr.add_subparsers(dest="prefs_cmd", required=True)
    ps = psub.add_parser("set", help="apply changes from a JSON object as a new preferences version")
    ps.add_argument("path")
    s = sub.add_parser("serve", help="start the web UI")
    s.add_argument("--port", type=int, default=8765)
    args = ap.parse_args()
    conn = connect(DB_PATH)
    if args.cmd == "seed":
        print(f"boards added: {load_seed(conn, SEED_CSV)}, sector overrides: {load_sectors(conn, SECTORS_CSV)}")
    elif args.cmd == "poll":
        poll(conn, sources=args.source, force=args.force)
    elif args.cmd == "relang":
        rows = conn.execute("SELECT id, title, description FROM jobs").fetchall()
        conn.executemany("UPDATE jobs SET lang = ? WHERE id = ?",
                         [(detect_lang(r["title"], r["description"]), r["id"]) for r in rows])
        conn.commit()
        print(f"languages set for {len(rows)} jobs")
    elif args.cmd == "reclassify":
        load_sectors(conn, SECTORS_CSV)
        print(f"jobs classified: {reclassify_jobs(conn)}, companies: {company_sectors(conn)}")
    elif args.cmd == "match" and args.match_cmd == "rescore":
        moved = rescore(conn)
        print("verdicts changed: " + (", ".join(f"{k}: {n}" for k, n in moved.items()) or "none"))
    elif args.cmd == "match" and args.match_cmd == "todo":
        work = matcher.todo(conn)
        Path(args.path).write_text(json.dumps(work, ensure_ascii=False, indent=1))
        print(f"jobs to score: {len(work['jobs'])} (written to {args.path}); ads too short to judge: {work['needs_ad']}")
    elif args.cmd == "match" and args.match_cmd == "results":
        saved, refused = matcher.save_results(conn, json.loads(Path(args.path).read_text()))
        print(f"evaluations saved: {saved}" + "".join(f"\nrefused {r}" for r in refused))
    elif args.cmd == "match":
        path = Path(args.path)
        rows = json.loads(path.read_text())
        print(f"evaluations imported: {import_results(conn, rows, run=args.run or path.stem)} of {len(rows)}")
    elif args.cmd == "cv" and args.cv_cmd == "pdfs":
        for job_id in sorted(cvs.ready(conn)):
            if path := cvs.save_pdf(conn, job_id):
                print(path)
    elif args.cmd == "cv" and args.cv_cmd == "todo":
        work = cvs.todo(conn)
        Path(args.path).write_text(json.dumps(work, ensure_ascii=False, indent=1))
        print(f"CVs to write: {len(work)} (written to {args.path})")
    elif args.cmd == "cv" and args.cv_cmd == "save":
        items = json.loads(Path(args.path).read_text())
        for item in items if isinstance(items, list) else [items]:
            rid, found = cvs.save(conn, item)
            print(f"job {item['job_id']}: " + (f"saved CV {rid}" if rid else "refused: " + "; ".join(found)))
    elif args.cmd == "prefs":
        changes, version = prefs.update(conn, json.loads(Path(args.path).read_text()))
        print(f"preferences version {version}: " + ("; ".join(changes) if changes else "nothing valid to change"))
    elif args.cmd == "cv":
        pack = sources.build(Path(args.src))
        sources.PACK.write_text(pack)
        print(f"wrote {sources.PACK} ({len(pack)} characters, links: {', '.join(k for k, _ in sources.links(pack))})")
    else:
        import logging

        import uvicorn

        from .web.app import create_app
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
        uvicorn.run(create_app(DB_PATH), host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()
