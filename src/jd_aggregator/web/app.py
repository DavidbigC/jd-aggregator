import logging
import subprocess
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlencode

import httpx
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.concurrency import run_in_threadpool

from .. import deepseek, keystore, prefs
from ..config import SECTORS_CSV
from ..cv import CONTACT, get_setting, pdf, set_setting
from ..cv import runner as cvs
from ..cv.tailor import HEADINGS, NAME
from ..db import connect
from ..lang import NAMES
from ..match import SHOWN, VERDICTS, set_label
from ..match import evaluate
from ..match import runner as matcher
from ..normalize import ISO
from ..registry import save_sector
from ..runner import SOURCES, poll
from . import queries

HERE = Path(__file__).parent
log = logging.getLogger(__name__)
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


def _check_key(key: str) -> tuple[str | None, str | None]:
    """(balance text, error) from DeepSeek's free balance endpoint."""
    try:
        b = deepseek.balance(key)
    except httpx.HTTPStatusError as e:
        return None, f"DeepSeek rejected this key ({e.response.status_code})."
    except httpx.HTTPError:
        return None, "Couldn't reach DeepSeek. Check your internet connection and try again."
    text = " · ".join(f"{i['currency']} {i['total_balance']}" for i in b.get("balance_infos", [])) or "none"
    return (text if b.get("is_available") else f"{text} (top up to make calls)"), None


async def _form(request: Request) -> dict:
    return {k: v[-1] for k, v in parse_qs((await request.body()).decode()).items()}


def create_app(db_path, sectors_csv=SECTORS_CSV) -> FastAPI:
    app = FastAPI(title="JD Aggregator")
    templates = Jinja2Templates(directory=HERE / "templates")
    templates.env.filters["ago"] = ago
    templates.env.filters["tilde"] = lambda p: str(p).replace(str(Path.home()), "~", 1)
    app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")

    def partial(request: Request) -> bool:
        return bool(request.headers.get("HX-Request")) and not request.headers.get("HX-History-Restore-Request")

    @app.get("/", response_class=HTMLResponse)
    def jobs(request: Request, q: str = "", posted: str = "7d", region: str = "", remote: str = "",
             source: str = "", company: int | None = None, stale: bool = False, sort: str = "posted", page: int = 0,
             lang: list[str] = Query([]), sector: str = "crypto", role: list[str] = Query([]),
             seniority: list[str] = Query([]), country: str = "", salary: bool = False, exclude: str = ""):
        f = queries.Filters(q, posted, region, remote, source, company, stale, sort, lang, sector, role, seniority,
                            country, salary, exclude)
        with closing(connect(db_path)) as conn:
            rows, total = queries.search_jobs(conn, f, limit=PAGE, offset=page * PAGE)
            stats, facets = queries.header_stats(conn), queries.facets(conn, sector)
        params = [(k, v) for k, v in request.query_params.multi_items() if k != "page"]
        ctx = {"jobs": rows, "total": total, "f": f, "more": (page + 1) * PAGE < total, "stats": stats,
               "next_url": "/?" + urlencode([*params, ("page", page + 1)]), "source_groups": queries.SOURCE_GROUPS,
               "facets": facets, "lang_names": NAMES, "nav": "jobs"}
        name = ("_job_rows.html" if page else "_results.html") if partial(request) else "jobs.html"
        return templates.TemplateResponse(request, name, ctx)

    @app.get("/jobs/{job_id}", response_class=HTMLResponse)
    def job(request: Request, job_id: int):
        with closing(connect(db_path)) as conn:
            j, sightings = queries.job_detail(conn, job_id)
            if not j:
                raise HTTPException(404)
            stats, cv = queries.header_stats(conn), cvs.view(conn, j)
        name = "_job_detail.html" if partial(request) else "job.html"
        return templates.TemplateResponse(request, name, {"job": j, "sightings": sightings, "stats": stats,
                                                          "nav": "jobs", **cv})

    def cv_section(request: Request, job_id: int, **ctx):
        with closing(connect(db_path)) as conn:
            j, _ = queries.job_detail(conn, job_id)
            if not j:
                raise HTTPException(404)
            cv = cvs.view(conn, j)
        return templates.TemplateResponse(request, "_cv.html", {"job": j, **cv, **ctx})

    @app.get("/jobs/{job_id}/cv/section", response_class=HTMLResponse)
    def cv_status(request: Request, job_id: int):
        return cv_section(request, job_id)

    def done_view(job_id: int) -> dict:
        with closing(connect(db_path)) as conn:
            j, _ = queries.job_detail(conn, job_id)
            view = cvs.view(conn, j) if j else None
        if not view or not view["cv"] or view["cv"]["status"] != "done":
            raise HTTPException(404, "No tailored CV for this job yet.")
        return view

    @app.get("/jobs/{job_id}/cv.pdf")
    def cv_pdf(job_id: int):
        """Re-render (so a changed contact line is picked up), save to the CV folder, and download."""
        path = pdf.save(done_view(job_id))
        return FileResponse(path, media_type="application/pdf", filename=path.name)

    @app.post("/jobs/{job_id}/cv/reveal")
    def cv_reveal(job_id: int):
        view = done_view(job_id)
        path = view["pdf"] if view["pdf"].exists() else pdf.save(view)
        subprocess.run(["open", "-R", str(path)])
        return Response(status_code=204)

    @app.post("/cvs/folder")
    def cv_folder():
        pdf.CV_PDF_DIR.mkdir(parents=True, exist_ok=True)
        subprocess.run(["open", str(pdf.CV_PDF_DIR)])
        return Response(status_code=204)

    @app.get("/jobs/{job_id}/cv", response_class=HTMLResponse)
    def cv_page(request: Request, job_id: int, embed: bool = False):
        view = done_view(job_id)
        return templates.TemplateResponse(request, "cv_print.html", {
            "view": view, "embed": embed, "name": NAME, "headings": HEADINGS[view["cv"]["final"]["language"]]})

    @app.get("/companies", response_class=HTMLResponse)
    def companies(request: Request, q: str = ""):
        with closing(connect(db_path)) as conn:
            rows, stats = queries.companies(conn, q), queries.header_stats(conn)
        return templates.TemplateResponse(request, "companies.html", {"rows": rows, "q": q, "stats": stats,
                                                                      "nav": "companies"})

    @app.post("/companies/{company_id}/sector/{sector}", response_class=HTMLResponse)
    def set_sector(request: Request, company_id: int, sector: str):
        if sector not in ("crypto", "other"):
            raise HTTPException(400)
        with closing(connect(db_path)) as conn:
            save_sector(conn, sectors_csv, company_id, sector, "ui")
            c = conn.execute("SELECT id, sector, sector_source FROM companies WHERE id = ?", (company_id,)).fetchone()
        return templates.TemplateResponse(request, "_sector.html", {"c": dict(c)})

    @app.get("/shortlist", response_class=HTMLResponse)
    def shortlist(request: Request, unlabelled: str = "", verdict: str = "", track: str = ""):
        with closing(connect(db_path)) as conn:
            groups, stats = queries.shortlist(conn, bool(unlabelled), verdict, track), queries.header_stats(conn)
            ctx = {"groups": groups, "unlabelled": bool(unlabelled), "verdict": verdict, "track": track,
                   "verdicts": VERDICTS, "tracks": queries.tracks(conn), "agreement": queries.agreement(conn),
                   "waiting": len(matcher.plan(conn)["todo"]), "last": matcher.last_run(conn),
                   "stats": stats, "nav": "shortlist", **cv_batch_ctx(conn)}
        return templates.TemplateResponse(request, "shortlist.html", ctx)

    def cv_batch_ctx(conn) -> dict:
        ready = cvs.ready(conn)
        shown = {r[0] for r in conn.execute(
            f"SELECT job_id FROM match_evaluations WHERE verdict IN ({', '.join('?' * len(SHOWN))})", SHOWN)}
        return {"cv_ready_ids": ready, "cv_ready": len(ready & shown), "cv_todo": len(cvs.todo_ids(conn)),
                "cv_folder": pdf.CV_PDF_DIR}

    @app.post("/shortlist/{job_id}/label", response_class=HTMLResponse)
    async def label(request: Request, job_id: int):
        form = parse_qs((await request.body()).decode())
        value, note = form.get("label", [""])[-1], form.get("note", [""])[-1]
        with closing(connect(db_path)) as conn:
            try:
                set_label(conn, job_id, value, note)
            except ValueError:
                raise HTTPException(400)
            e = queries.evaluation(conn, job_id)
        if not e:
            raise HTTPException(404)
        return templates.TemplateResponse(request, "_label.html", {"e": e})

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

    def key_card(request: Request, **ctx):
        key, source = keystore.get_key()
        return templates.TemplateResponse(request, "_deepseek.html", {
            "key_set": bool(key), "source": source, "tail": key[-4:] if key else "", **ctx})

    @app.get("/settings", response_class=HTMLResponse)
    def settings(request: Request):
        key, source = keystore.get_key()
        with closing(connect(db_path)) as conn:
            stats, contact = queries.header_stats(conn), get_setting(conn, CONTACT)
        return templates.TemplateResponse(request, "settings.html", {
            "key_set": bool(key), "source": source, "tail": key[-4:] if key else "", "stats": stats,
            "contact": contact, "nav": "settings"})

    @app.post("/settings/cv-contact", response_class=HTMLResponse)
    async def save_contact(request: Request):
        contact = " ".join((await _form(request)).get("contact", "").split())[:200]
        with closing(connect(db_path)) as conn:
            set_setting(conn, CONTACT, contact)
        return templates.TemplateResponse(request, "_cv_contact.html", {"contact": contact, "saved": True})

    @app.post("/settings/deepseek", response_class=HTMLResponse)
    async def save_key(request: Request):
        key = (await _form(request)).get("key", "").strip()
        if not keystore.KEY_RE.match(key):
            return key_card(request, checked=True, error="That doesn't look like a DeepSeek key. It starts with sk-.")
        balance, error = await run_in_threadpool(_check_key, key)
        if error:
            return key_card(request, checked=True, error=error)
        keystore.set_key(key)
        return key_card(request, checked=True, balance=balance)

    @app.post("/settings/deepseek/test", response_class=HTMLResponse)
    def test_key(request: Request):
        key, _ = keystore.get_key()
        if not key:
            return key_card(request)
        balance, error = _check_key(key)
        return key_card(request, checked=True, balance=balance, error=error)

    @app.post("/settings/deepseek/delete", response_class=HTMLResponse)
    async def delete_key(request: Request):
        if not (await _form(request)).get("confirm"):
            return key_card(request, checked=True, confirm=True)
        keystore.delete_key()
        return key_card(request)

    @app.get("/preferences", response_class=HTMLResponse)
    def preferences(request: Request):
        with closing(connect(db_path)) as conn:
            p, version = prefs.current(conn)
            stats = queries.header_stats(conn)
        return templates.TemplateResponse(request, "preferences.html", {
            "summary": prefs.summary(p), "missing": len(prefs.missing(p)), "version": version,
            "profile": evaluate.PROFILE.read_text(),
            "stats": stats, "nav": "preferences"})

    return app
