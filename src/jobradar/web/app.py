from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ..db import connect
from ..lang import NAMES
from ..normalize import ISO
from ..runner import SOURCES, poll
from . import queries

HERE = Path(__file__).parent
PAGE = 50


def ago(iso: str | None) -> str:
    if not iso:
        return "—"
    secs = (datetime.now(timezone.utc) - datetime.strptime(iso, ISO).replace(tzinfo=timezone.utc)).total_seconds()
    for unit, size in (("d", 86400), ("h", 3600), ("m", 60)):
        if secs >= size:
            return f"{int(secs // size)}{unit} ago"
    return "just now"


def _run_in_background(db_path, name: str) -> None:
    with closing(connect(db_path)) as conn:
        poll(conn, sources=[name], force=True, log=lambda _: None)


def create_app(db_path) -> FastAPI:
    app = FastAPI(title="Job Radar")
    templates = Jinja2Templates(directory=HERE / "templates")
    templates.env.filters["ago"] = ago
    app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")

    def partial(request: Request) -> bool:
        return bool(request.headers.get("HX-Request")) and not request.headers.get("HX-History-Restore-Request")

    @app.get("/", response_class=HTMLResponse)
    def jobs(request: Request, q: str = "", posted: str = "7d", region: str = "", remote: bool = False,
             source: str = "", company: int | None = None, stale: bool = False, sort: str = "posted", page: int = 0,
             lang: list[str] = Query([])):
        f = queries.Filters(q, posted, region, remote, source, company, stale, sort, lang)
        with closing(connect(db_path)) as conn:
            rows, total = queries.search_jobs(conn, f, limit=PAGE, offset=page * PAGE)
            stats, langs = queries.header_stats(conn), queries.languages(conn)
        params = [(k, v) for k, v in request.query_params.multi_items() if k != "page"]
        ctx = {"jobs": rows, "total": total, "f": f, "more": (page + 1) * PAGE < total, "stats": stats,
               "next_url": "/?" + urlencode([*params, ("page", page + 1)]), "source_groups": queries.SOURCE_GROUPS,
               "langs": langs, "lang_names": NAMES, "nav": "jobs"}
        name = ("_job_rows.html" if page else "_results.html") if partial(request) else "jobs.html"
        return templates.TemplateResponse(request, name, ctx)

    @app.get("/jobs/{job_id}", response_class=HTMLResponse)
    def job(request: Request, job_id: int):
        with closing(connect(db_path)) as conn:
            j, sightings = queries.job_detail(conn, job_id)
            stats = queries.header_stats(conn)
        if not j:
            raise HTTPException(404)
        name = "_job_detail.html" if partial(request) else "job.html"
        return templates.TemplateResponse(request, name, {"job": j, "sightings": sightings, "stats": stats,
                                                          "nav": "jobs"})

    @app.get("/companies", response_class=HTMLResponse)
    def companies(request: Request, q: str = ""):
        with closing(connect(db_path)) as conn:
            rows, stats = queries.companies(conn, q), queries.header_stats(conn)
        return templates.TemplateResponse(request, "companies.html", {"rows": rows, "q": q, "stats": stats,
                                                                      "nav": "companies"})

    @app.get("/sources", response_class=HTMLResponse)
    def sources(request: Request):
        with closing(connect(db_path)) as conn:
            rows = queries.sources_status(conn, SOURCES)
            by_ats, failing = queries.boards_summary(conn)
            stats = queries.header_stats(conn)
        return templates.TemplateResponse(request, "sources.html", {"rows": rows, "by_ats": by_ats,
                                                                    "failing": failing, "stats": stats,
                                                                    "nav": "sources"})

    @app.post("/sources/{name}/run", response_class=HTMLResponse)
    def run_now(name: str, background: BackgroundTasks):
        if name not in SOURCES:
            raise HTTPException(404)
        background.add_task(_run_in_background, db_path, name)
        return HTMLResponse('<span class="muted">queued — refresh in a minute</span>')

    return app
