import argparse
import json
from pathlib import Path

from .classify import company_sectors, reclassify_jobs
from .config import DB_PATH, SECTORS_CSV, SEED_CSV
from .db import connect
from .lang import detect_lang
from .match import import_results
from .registry import load_sectors, load_seed
from .runner import poll


def main() -> None:
    ap = argparse.ArgumentParser(prog="jobradar")
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
    elif args.cmd == "match":
        path = Path(args.path)
        rows = json.loads(path.read_text())
        print(f"evaluations imported: {import_results(conn, rows, run=args.run or path.stem)} of {len(rows)}")
    else:
        import uvicorn

        from .web.app import create_app
        uvicorn.run(create_app(DB_PATH), host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()
