import json
import logging
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlencode

import httpx
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.concurrency import run_in_threadpool

from .. import deepseek, keystore, prefs
from ..config import PREFS_PROMPT, SECTORS_CSV
from ..db import connect
from ..lang import NAMES
from ..match import VERDICTS, set_label
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


def _msg(m: dict) -> dict:
    return {**m, "changes": prefs.describe_change(json.loads(m["proposal"])) if m.get("proposal") else []}


async def _form(request: Request) -> dict:
    return {k: v[-1] for k, v in parse_qs((await request.body()).decode()).items()}


def create_app(db_path, sectors_csv=SECTORS_CSV) -> FastAPI:
    app = FastAPI(title="Job Radar")
    templates = Jinja2Templates(directory=HERE / "templates")
    templates.env.filters["ago"] = ago
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

    @app.post("/companies/{company_id}/sector/{sector}", response_class=HTMLResponse)
    def set_sector(request: Request, company_id: int, sector: str):
        if sector not in ("crypto", "other"):
            raise HTTPException(400)
        with closing(connect(db_path)) as conn:
            save_sector(conn, sectors_csv, company_id, sector, "ui")
            c = conn.execute("SELECT id, sector, sector_source FROM companies WHERE id = ?", (company_id,)).fetchone()
        return templates.TemplateResponse(request, "_sector.html", {"c": dict(c)})

    def run_panel(request: Request, conn, **ctx):
        key, _ = keystore.get_key()
        run = matcher.running(conn)
        return templates.TemplateResponse(request, "_match_run.html", {
            "has_key": bool(key), "run": run, "last": None if run else matcher.last_run(conn), **ctx})

    @app.get("/shortlist", response_class=HTMLResponse)
    def shortlist(request: Request, unlabelled: str = "", verdict: str = "", track: str = ""):
        key, _ = keystore.get_key()
        with closing(connect(db_path)) as conn:
            groups, stats = queries.shortlist(conn, bool(unlabelled), verdict, track), queries.header_stats(conn)
            run = matcher.running(conn)
            ctx = {"groups": groups, "unlabelled": bool(unlabelled), "verdict": verdict, "track": track,
                   "verdicts": VERDICTS, "tracks": queries.tracks(conn), "agreement": queries.agreement(conn),
                   "has_key": bool(key), "run": run, "last": None if run else matcher.last_run(conn),
                   "stats": stats, "nav": "shortlist"}
        return templates.TemplateResponse(request, "shortlist.html", ctx)

    @app.post("/shortlist/run", response_class=HTMLResponse)
    async def run_matcher(request: Request):
        def check():
            with closing(connect(db_path)) as conn:
                return matcher.plan(conn)
        p = await run_in_threadpool(check)
        with closing(connect(db_path)) as conn:
            return run_panel(request, conn, plan=p, sample=matcher.SAMPLE)

    @app.post("/shortlist/run/start", response_class=HTMLResponse)
    async def start_matcher(request: Request):
        limit = (await _form(request)).get("limit", "")
        key, _ = keystore.get_key()
        error = None
        if not key:
            error = "Add your DeepSeek API key in Settings first."
        else:
            try:
                await run_in_threadpool(matcher.start, db_path, key, int(limit) if limit.isdigit() else None)
            except matcher.AlreadyRunning:
                error = "A run is already in progress."
        with closing(connect(db_path)) as conn:
            return run_panel(request, conn, error=error)

    @app.get("/shortlist/run/status", response_class=HTMLResponse)
    def matcher_status(request: Request):
        with closing(connect(db_path)) as conn:
            if not matcher.running(conn):
                return HTMLResponse("", headers={"HX-Refresh": "true"})
            return run_panel(request, conn)

    @app.get("/shortlist/run/panel", response_class=HTMLResponse)
    def matcher_panel(request: Request):
        with closing(connect(db_path)) as conn:
            return run_panel(request, conn)

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
            stats = queries.header_stats(conn)
        return templates.TemplateResponse(request, "settings.html", {
            "key_set": bool(key), "source": source, "tail": key[-4:] if key else "", "stats": stats,
            "nav": "settings"})

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
        key, _ = keystore.get_key()
        with closing(connect(db_path)) as conn:
            p, version = prefs.current(conn)
            msgs, stats = prefs.messages(conn), queries.header_stats(conn)
        return templates.TemplateResponse(request, "preferences.html", {
            "summary": prefs.summary(p), "missing": len(prefs.missing(p)), "version": version,
            "msgs": [_msg(m) for m in msgs], "has_key": bool(key), "profile": evaluate.PROFILE.read_text(),
            "stats": stats, "nav": "preferences"})

    def chat_turn(key: str, text: str) -> list[dict]:
        with closing(connect(db_path)) as conn:
            return prefs.reply(conn, key, PREFS_PROMPT.read_text(), text)

    @app.post("/preferences/chat", response_class=HTMLResponse)
    async def chat(request: Request):
        key, _ = keystore.get_key()
        text = (await _form(request)).get("text", "").strip()[:2000]
        error = None
        if not key:
            error = "Add your DeepSeek API key in Settings first."
        else:
            try:
                new = await run_in_threadpool(chat_turn, key, text)
            except httpx.HTTPStatusError as e:
                log.exception("preferences chat failed; message was %r", text[:300])
                error = f"DeepSeek returned an error ({e.response.status_code}). Check your key and balance in Settings."
            except (httpx.HTTPError, ValueError):
                log.exception("preferences chat failed; message was %r", text[:300])
                error = "DeepSeek didn't answer properly. Your message is still in the box; please send it again."
        if error:
            return templates.TemplateResponse(request, "_chat_msg.html", {"m": {
                "id": "error", "role": "assistant error", "content": error}}, headers={"X-Chat-Error": "1"})
        return HTMLResponse("".join(templates.get_template("_chat_msg.html").render(m=_msg(m)) for m in new))

    def proposal_response(request: Request, msg_id: int, ok: bool):
        if not ok:
            raise HTTPException(404)
        with closing(connect(db_path)) as conn:
            m = dict(conn.execute("SELECT * FROM pref_messages WHERE id = ?", (msg_id,)).fetchone())
            p, version = prefs.current(conn)
        summary = templates.get_template("_prefs_summary.html").render(
            summary=prefs.summary(p), missing=len(prefs.missing(p)), version=version, oob=True)
        return HTMLResponse(templates.get_template("_chat_msg.html").render(m=_msg(m)) + summary)

    @app.post("/preferences/proposal/{msg_id}/apply", response_class=HTMLResponse)
    def apply_proposal(request: Request, msg_id: int):
        with closing(connect(db_path)) as conn:
            ok = prefs.apply(conn, msg_id)
        return proposal_response(request, msg_id, ok)

    @app.post("/preferences/proposal/{msg_id}/discard", response_class=HTMLResponse)
    def discard_proposal(request: Request, msg_id: int):
        with closing(connect(db_path)) as conn:
            ok = prefs.discard(conn, msg_id)
        return proposal_response(request, msg_id, ok)

    @app.post("/preferences/new", response_class=HTMLResponse)
    def new_conversation(request: Request):
        key, _ = keystore.get_key()
        with closing(connect(db_path)) as conn:
            prefs.new_conversation(conn)
        return templates.TemplateResponse(request, "_chat_log.html", {"msgs": [], "has_key": bool(key)})

    return app
